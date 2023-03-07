# fixes stubs like redis that use generics when the code does not
from __future__ import annotations

import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis.asyncio.client import Redis

from nifty_common import cfg
from nifty_common.helpers import none_throws, noneint_throws, optint_or_none
from nifty_common.types import Key, RedisType

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def get_redis(
    redis_type: RedisType,
) -> Redis[str]:
    print(redis_type.cfg_key)
    return Redis(
        host=cfg.g(redis_type.cfg_key, "host"),
        username=cfg.g(redis_type.cfg_key, "user"),
        password=cfg.g(redis_type.cfg_key, "pwd"),
        port=cfg.gint_fb(redis_type.cfg_key, "port", 6379),
        decode_responses=True,
    )


async def rint(
    redis: Redis[str], key: str, throws: Optional[bool] = True
) -> Optional[int]:
    raw = await redis.get(key)
    return noneint_throws(raw, key) if throws else optint_or_none(raw)


async def robj(
    redis: Redis[str],
    key: str,
    cl: Type[TBaseModel],
    throws: Optional[bool] = True,
) -> Optional[TBaseModel]:
    raw = await redis.hgetall(key)
    logging.debug(f"Raw HGETALL response: {raw}")
    if throws:
        return cl.parse_obj(none_throws(raw, key))

    return cl.parse_obj(raw) if raw else None


async def trending_size(
    redis: Redis[str], throws: Optional[bool] = True
) -> Optional[int]:
    return await rint(redis, Key.trending_size, throws)
