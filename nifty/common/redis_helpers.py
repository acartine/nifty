# fixes stubs like redis that use generics when the code does not
from __future__ import annotations

import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis.client import Redis

from . import cfg
from .helpers import none_throws, noneint_throws
from .types import Key, RedisType

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def get_redis(
    redis_type: RedisType, *, cfg_creds_section: Optional[str] = None
) -> Redis[str]:
    creds_section = redis_type.cfg_key
    user_key = "user"
    pwd_key = "pwd"
    if cfg_creds_section:
        creds_section = cfg_creds_section
        user_key = "redis_user"
        pwd_key = "redis_pwd"
    foo = Redis(
        host=cfg.g(redis_type.cfg_key, "host"),
        username=cfg.g(creds_section, user_key),
        password=cfg.g(creds_section, pwd_key),
        port=cfg.gint_fb(redis_type.cfg_key, "port", 6379),
        decode_responses=True,
    )
    return foo


def rint_throws(redis: Redis[str], key: str) -> int:
    raw = redis.get(key)
    return noneint_throws(raw, key)


def rint(redis: Redis[str], key: str) -> Optional[int]:
    raw = redis.get(key)
    return int(raw) if raw is not None else None


def robj(
    redis: Redis[str],
    key: str,
    cl: Type[TBaseModel],
    throws: Optional[bool] = True,
) -> Optional[TBaseModel]:
    raw = redis.hgetall(key)
    logging.getLogger().debug(f"Raw HGETALL response: {raw}")
    if throws:
        return cl.parse_obj(none_throws(raw, key))

    return cl.parse_obj(raw) if raw else None


def trending_size(
    redis: Redis[str],
) -> Optional[int]:
    return rint_throws(redis, Key.trending_size)
