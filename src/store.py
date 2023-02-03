import logging
import atexit
from dataclasses import dataclass
from typing import Tuple, TypeVar

from redis_lru import RedisLRU

from config import cfg

from psycopg.rows import class_row, BaseRowFactory
from psycopg_pool import ConnectionPool
from redis import Redis

_logger = logging.getLogger(__name__)
T = TypeVar('T')
_conninfo = f"postgresql://{cfg['postgres']['user']}:{cfg['postgres']['pwd']}" \
            f"@{cfg['postgres']['host']}/postgres"
_pool = ConnectionPool(conninfo=_conninfo)

redis_client = Redis(host=cfg['redis']['host'], username=cfg['redis']['user'],
                     password=cfg['redis']['pwd'])
_long_url_cache = RedisLRU(redis_client)


@atexit.register
def close():
    _pool.close()


@dataclass
class LinkUpsertResult:
    id: int
    long_url_id: int
    short_url_id: int
    long_url: str
    short_url: str


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
             row_factory: BaseRowFactory[T]) -> T:
    _logger.debug(args)
    with _pool.connection() as conn:
        with conn.cursor(row_factory=row_factory) as cur:
            cur.execute(sql, args)
            return cur.fetchone()


_short_url_sql = """
SELECT s.url
FROM link k
JOIN short_url s ON s.id = k.short_url_id
JOIN long_url l ON l.id = k.long_url_id
WHERE l.url = %s;
"""


def get_short_url(long_url: str) -> str | None:
    ret = _execute(_short_url_sql, (long_url,), class_row(Url))
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
    ret = _execute(_upsert_long_url_sql, (long_url, long_url), class_row(Id))
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
VALUES (%s, COALESCE((SELECT id FROM upsert_short),(SELECT id FROM short_url WHERE url = %s)))
ON CONFLICT (short_url_id)
DO NOTHING
RETURNING id, %s AS long_url_id, short_url_id, %s AS short_url
)
SELECT ul.id, %s AS long_url_id, ul.short_url_id, l.url AS long_url, ul.short_url
FROM upsert_link ul
JOIN long_url l
ON l.id = %s AND l.id = ul.long_url_id;
    """


def upsert_link(long_url_id: int, short_url: str) -> LinkUpsertResult:
    params = (short_url, long_url_id, short_url, long_url_id, short_url,
              long_url_id, long_url_id)
    ret = _execute(_link_sql, params, class_row(LinkUpsertResult))
    if not ret:
        raise Exception("Unable to get or create long url from ${long_url}")

    # update the cache, otherwise it's memoized to None
    _long_url_cache.set(ret.short_url, ret.long_url)
    return ret


_long_url_sql = """
SELECT l.url
FROM short_url s
JOIN link k
ON s.url = %s AND s.id = k.short_url_id
JOIN long_url l
ON l.id = k.long_url_id;
    """


@_long_url_cache
def get_long_url(short_url: str) -> str | None:
    ret = _execute(_long_url_sql, (short_url,), class_row(Url))
    return ret.url if ret else None
