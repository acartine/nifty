# fixes stubs like redis that use generics when the code does not
from __future__ import annotations

import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis.asyncio import client

from nifty.common import cfg
from nifty.common.helpers import none_throws, noneint_throws, optint_or_none
from nifty.common.types import Key, RedisType

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def get_redis(
    redis_type: RedisType, *, cfg_creds_section: Optional[str] = None
) -> client.Redis[str]:
    creds_section = redis_type.cfg_key
    user_key = "user"
    pwd_key = "pwd"
    if cfg_creds_section:
        creds_section = cfg_creds_section
        user_key = "redis_user"
        pwd_key = "redis_pwd"
    return client.Redis(
        host=cfg.g(redis_type.cfg_key, "host"),
        username=cfg.g(creds_section, user_key),
        password=cfg.g(creds_section, pwd_key),
        port=cfg.gint_fb(redis_type.cfg_key, "port", 6379),
        decode_responses=True,
    )


async def rint(
    redis: client.Redis[str], key: str, throws: Optional[bool] = True
) -> Optional[int]:
    raw = await redis.get(key)
    return noneint_throws(raw, key) if throws else optint_or_none(raw)


async def robj(
    redis: client.Redis[str],
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
    redis: client.Redis[str], throws: Optional[bool] = True
) -> Optional[int]:
    return await rint(redis, Key.trending_size, throws)
