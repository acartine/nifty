import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis.client import Redis

from nifty_common import cfg
from nifty_common.helpers import none_throws, noneint_throws
from nifty_common.types import Key, RedisType

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)

# redis typing makes this difficult for now
# pyright: reportMissingTypeArgument=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false


def get_redis(redis_type: RedisType) -> Redis:
    print(redis_type.cfg_key)
    foo = Redis(
        host=cfg.g(redis_type.cfg_key, "host"),
        username=cfg.g(redis_type.cfg_key, "user"),
        password=cfg.g(redis_type.cfg_key, "pwd"),
        port=cfg.gint_fb(redis_type.cfg_key, "port", 6379),
        decode_responses=True,
    )
    return foo


def rint_throws(redis: Redis, key: str) -> int:
    raw = redis.get(key)
    return noneint_throws(raw, key)


def rint(redis: Redis, key: str) -> Optional[int]:
    raw = redis.get(key)
    return int(raw) if raw is not None else None


def robj(
    redis: Redis,
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
    redis: Redis,
) -> Optional[int]:
    return rint_throws(redis, Key.trending_size)
