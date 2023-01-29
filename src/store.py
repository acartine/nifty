import logging
import os
from dataclasses import dataclass
from typing import Tuple, TypeVar

import psycopg
from psycopg.rows import class_row, BaseRowFactory

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class LinkUpsertResult:
    id: int | None = None
    short_url_id: int | None = None


@dataclass
class Id:
    id: int | None = None


@dataclass
class Url:
    url: str | None = None


def __execute(sql: str,
              args: Tuple,
              row_factory: BaseRowFactory[T]) -> T:
    host = os.environ['PG_HOST']
    user = os.environ['PG_USER']
    secret = os.environ[f"{user.upper()}_PWD"]
    conninfo = f"postgresql://{user}:****@{host}/postgres"
    logger.debug(f"DB = {conninfo}")
    logger.debug(args)
    with psycopg.connect(conninfo=conninfo.replace('****', secret),
                         row_factory=row_factory) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()


# def __get_row_from_cur(cur: Cursor) -> Row | None:
#     return cur.fetchone()
#
#
# def __get_val_from_cur(cur: Cursor) -> Any:
#     row = __get_row_from_cur(cur)
#     return row[0] if row else None
#
#
# def __get_val(sql: str, args: Tuple) -> Any | None:
#     return __execute(sql, args, __get_val_from_cur)


def get_short_url(long_url: str) -> str | None:
    # TODO add redis cache
    sql = """
SELECT s.url
FROM link k
JOIN short_url s ON s.id = k.short_url_id
JOIN long_url l ON l.id = k.long_url_id
WHERE l.url = %s;
"""
    ret = __execute(sql, (long_url,), class_row(Url))
    return ret.url if ret else None


def upsert_long_url(long_url: str) -> int:
    sql = """
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
    ret = __execute(sql, (long_url, long_url), class_row(Id))
    if not ret:
        raise Exception("Unable to get or create long url from ${long_url}")

    return ret.id


def upsert_link(long_url_id: int, short_url: str) -> LinkUpsertResult:
    sql = """
WITH upsert_short AS (
  INSERT
    INTO
      short_url (url)
    VALUES (%s)
ON
    CONFLICT (url) DO NOTHING 
RETURNING id 
)
INSERT INTO link(long_url_id, short_url_id)
VALUES (%s, COALESCE((SELECT id FROM upsert_short),(SELECT id FROM short_url WHERE url = %s)))
ON CONFLICT (short_url_id)
DO NOTHING
RETURNING id, short_url_id;
    """
    ret = __execute(sql, (short_url, long_url_id, short_url),
                    class_row(LinkUpsertResult))
    if not ret:
        raise Exception("Unable to get or create long url from ${long_url}")

    return ret


def get_long_url(short_url: str) -> str | None:
    sql = """
SELECT l.url
FROM short_url s
JOIN link k
ON s.url = %s AND s.id = k.short_url_id
JOIN long_url l
ON l.id = k.long_url_id;
    """
    ret = __execute(sql, (short_url,), class_row(Url))
    return ret.url if ret else None
