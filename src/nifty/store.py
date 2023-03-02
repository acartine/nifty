import atexit
import logging
from typing import Callable, List, Optional, Tuple, TypeVar

from psycopg import Cursor
from psycopg.rows import BaseRowFactory, class_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

from nifty_common import cfg
from nifty_common.helpers import retry
from nifty_common.redis_helpers import get_redis, rint, robj, trending_size
from nifty_common.types import Key, Link, RedisType

_logger = logging.getLogger(__name__)
T = TypeVar('T')
R = TypeVar('R')
_conninfo = f"postgresql://{cfg.get('postgres', 'user')}:{cfg.get('postgres', 'pwd')}" \
            f"@{cfg.get('postgres', 'host')}/postgres"
_pool = ConnectionPool(conninfo=_conninfo)
redis_client = get_redis(RedisType.STD)
cache = get_redis(RedisType.CACHE)


@atexit.register
def close():
    _pool.close()


class TrendingItem(BaseModel):
    id: int
    created_at: int
    long_url: str
    short_url: str
    views: int


class Trending(BaseModel):
    list: List[TrendingItem]


class Id(BaseModel):
    id: int | None = None


class Url(BaseModel):
    url: str | None = None


class UrlRow(BaseModel):
    id: int
    url: str


def _execute(sql: str,
             args: Tuple,
             row_factory: BaseRowFactory[T],
             processor: Callable[[Cursor[T]], R]) -> R:
    _logger.debug(args)
    with _pool.connection() as conn:
        with conn.cursor(row_factory=row_factory) as cur:
            cur.execute(sql, args)
            return processor(cur)


def _ex_one(sql: str,
            args: Tuple,
            row_factory: BaseRowFactory[T]) -> T:
    return _execute(sql, args, row_factory, lambda cur: cur.fetchone())


def _ex_all(sql: str,
            args: Tuple,
            row_factory: BaseRowFactory[T]) -> List[T]:
    return _execute(sql, args, row_factory, lambda cur: cur.fetchall())


_short_url_sql = """
SELECT s.url
FROM link k
JOIN short_url s ON s.id = k.short_url_id
JOIN long_url l ON l.id = k.long_url_id
WHERE l.url = %s;
"""


def get_short_url(long_url: str) -> str | None:
    ret = _ex_one(_short_url_sql, (long_url,), class_row(Url))
    return ret.url if ret else None


_upsert_long_url_sql = """
    WITH new_url AS(
      INSERT
        INTO
          long_url (url)
        VALUES (%s)
        ON
            CONFLICT (url) DO NOTHING 
        RETURNING id
    ) 
    SELECT
      COALESCE(
    (SELECT id FROM new_url),
    (SELECT id FROM long_url WHERE url = %s)) AS id;"""


def upsert_long_url(long_url: str) -> int:
    ret = _ex_one(_upsert_long_url_sql, (long_url, long_url), class_row(Id))
    if not ret:
        raise Exception("Unable to get or create long url from ${long_url}")

    return ret.id


_link_sql = """
WITH upsert_short AS (
  INSERT
    INTO
      short_url (url)
    VALUES (%s)
ON
    CONFLICT (url) DO NOTHING 
RETURNING id 
), upsert_link AS (
INSERT INTO link(long_url_id, short_url_id)
VALUES (%s, COALESCE((SELECT id FROM upsert_short),(SELECT id 
    FROM short_url WHERE url = %s)))
ON CONFLICT (short_url_id)
DO NOTHING
RETURNING id, created_at, %s AS long_url_id,
    short_url_id, %s AS short_url
)
SELECT ul.id, ul.created_at, %s AS long_url_id, ul.short_url_id,
        l.url AS long_url, ul.short_url
FROM upsert_link ul
JOIN long_url l
ON l.id = %s AND l.id = ul.long_url_id;
    """


@retry(max_tries=3, stack_id=__name__)
def _cache_upsert_link(link: Link):
    link_key = Key.link_by_link_id.sub(link.id)
    link_id_key = Key.link_id_cache.sub(link.short_url)
    long_url_key = Key.long_by_short.sub(link.short_url)
    with cache.pipeline() as p:
        p.watch(link_key, link_id_key, long_url_key)
        p.multi()
        p.hset(link_key, mapping=link.redis_dict()) \
            .set(link_id_key, link.id) \
            .set(long_url_key, link.long_url) \
            .execute()


def _get_link_from_cache(short_url: str) -> Optional[Link]:
    link_id_key = Key.link_id_cache.sub(short_url)

    # TODO make a lua script and execute both on server side
    # we want to do this atomically, but for now let's get this working
    link_id = rint(cache,
                   link_id_key,
                   throws=False)
    if link_id is not None:
        link_key = Key.link_by_link_id.sub(link_id)
        link = robj(cache, link_key, Link, throws=False)
        if link is None:
            _logger.debug(f"cache MISS - short_url:{short_url} , link_id:{link_id}")
            return None
        else:
            _logger.debug(f"cache HIT  - short_url:{short_url} , link_id:{link_id}")
            return link
    else:
        _logger.debug(f"CACHE MISS - no link_id for {short_url}")
        return None


def upsert_link(long_url_id: int, short_url: str) -> Link:
    link = _get_link_from_cache(short_url)
    if link is not None:
        return link

    params = (short_url, long_url_id, short_url, long_url_id, short_url,
              long_url_id, long_url_id)
    ret = _ex_one(_link_sql, params, class_row(Link))
    if not ret:
        raise Exception("Unable to get or create long url from ${long_url}")

    # update the cache, otherwise it's memoized to None
    _cache_upsert_link(ret)
    return ret


_long_url_sql = """
SELECT k.id,
    k.created_at,
    l.id as long_url_id, 
    s.id as short_url_id,
    l.url as long_url,
    s.url as short_url
FROM short_url s
JOIN link k
ON s.url = %s AND s.id = k.short_url_id
JOIN long_url l
ON l.id = k.long_url_id;
    """


def get_long_url(short_url: str) -> Link | None:
    link = _get_link_from_cache(short_url)
    if link is None:
        link = _ex_one(_long_url_sql, (short_url,), class_row(Link))
        if link is None:
            return None
        _cache_upsert_link(link)

    return link


links_by_ids_sql = """
SELECT k.id, 
    k.created_at,
    l.id as long_url_id, 
    s.id as short_url_id,
    l.url as long_url,
    s.url as short_url
FROM link k
JOIN short_url s
ON s.id = k.short_url_id
JOIN long_url l
ON l.id = k.long_url_id
WHERE k.id IN (
"""


def get_links_by_id(ids: List[int]) -> List[Link]:
    sql = links_by_ids_sql + ','.join(['%s'] * len(ids)) + ')'
    return _ex_all(sql, tuple(ids), class_row(Link))


def get_trending() -> Trending:
    tr_sz = trending_size(redis_client, throws=False)
    if tr_sz is None:
        return Trending(list=[])

    results: List[Tuple[int, int]] = \
        redis_client.zrange(Key.trending,
                            0, trending_size(redis_client),
                            desc=True,
                            withscores=True)
    _logger.debug(results)
    items: List[TrendingItem] = []
    if results and len(results) > 0:
        links: List[Link] = get_links_by_id([int(t[0]) for t in results])
        for i in range(len(results)):
            items.append(
                TrendingItem(id=results[i][0],
                             created_at=links[i].created_at_ms(),
                             long_url=links[i].long_url,
                             short_url=links[i].short_url,
                             views=int(results[i][1])
                             ))
    return Trending(list=items)
