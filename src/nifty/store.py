import atexit
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Tuple, TypeVar

from psycopg import Cursor
from psycopg.rows import BaseRowFactory, class_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from redis_lru import RedisLRU

from nifty_common.config import cfg
from nifty_common.constants import REDIS_TOPLIST_KEY
from nifty_common.helpers import get_redis

_logger = logging.getLogger(__name__)
T = TypeVar('T')
R = TypeVar('R')
_conninfo = f"postgresql://{cfg['postgres']['user']}:{cfg['postgres']['pwd']}" \
            f"@{cfg['postgres']['host']}/postgres"
_pool = ConnectionPool(conninfo=_conninfo)
redis_client = get_redis()
_long_url_cache = RedisLRU(redis_client)


@atexit.register
def close():
    _pool.close()


@dataclass
class Link:
    id: int
    created_at: datetime
    long_url_id: int
    short_url_id: int
    long_url: str
    short_url: str

    def created_at_ms(self) -> int:
        return int(self.created_at.timestamp()*1000)


class HotListItem(BaseModel):
    id: int
    created_at: int
    long_url: str
    short_url: str
    views: int


class HotList(BaseModel):
    list: List[HotListItem]


@dataclass
class Id:
    id: int | None = None


@dataclass
class Url:
    url: str | None = None


@dataclass
class UrlRow:
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


def upsert_link(long_url_id: int, short_url: str) -> Link:
    params = (short_url, long_url_id, short_url, long_url_id, short_url,
              long_url_id, long_url_id)
    ret = _ex_one(_link_sql, params, class_row(Link))
    if not ret:
        raise Exception("Unable to get or create long url from ${long_url}")

    # update the cache, otherwise it's memoized to None
    _long_url_cache.set(ret.short_url, ret)
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


@_long_url_cache
def get_long_url(short_url: str) -> Link | None:
    return _ex_one(_long_url_sql, (short_url,), class_row(Link))


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


def get_hotlinks() -> HotList:
    results: List[Tuple[int, int]] = redis_client.zrange(REDIS_TOPLIST_KEY,
                                                         0, 10,
                                                         withscores=True)
    _logger.debug(results)
    items: List[HotListItem] = []
    if results and len(results) > 0:
        links: List[Link] = get_links_by_id([int(t[0]) for t in results])
        for i in range(len(results)):
            items.append(HotListItem(id=results[i][0],
                                     created_at=links[i].created_at_ms(),
                                     long_url=links[i].long_url,
                                     short_url=links[i].short_url,
                                     views=int(results[i][1])
                                     ))
    return HotList(list=items)