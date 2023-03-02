import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis.asyncio.client import Redis as AsyncRedis
from redis.client import Redis

from nifty_common import cfg
from nifty_common.constants import REDIS_TRENDING_SIZE_KEY
from nifty_common.helpers import none_throws, noneint_throws, optint_or_none
from nifty_common.types import Key, RedisType

TBaseModel = TypeVar('TBaseModel', bound=BaseModel)


def get_redis(redis_type: RedisType) -> Redis:
    print(redis_type.cfg_key)
    return Redis(host=cfg.get(redis_type.cfg_key, 'host'),
                 username=cfg.get(redis_type.cfg_key, 'user'),
                 password=cfg.get(redis_type.cfg_key, 'pwd'),
                 port=cfg.getint(redis_type.cfg_key, 'port', 6379),
                 decode_responses=True)


def get_redis_async(redis_type: RedisType) -> AsyncRedis:
    return AsyncRedis(host=cfg.get(redis_type.cfg_key, 'host'),
                      username=cfg.get(redis_type.cfg_key, 'user'),
                      password=cfg.get(redis_type.cfg_key, 'pwd'),
                      decode_responses=True)


def rint(redis: Redis, key: str, throws: Optional[bool] = True) -> Optional[int]:
    raw = redis.get(key)
    return noneint_throws(raw, key) if throws else optint_or_none(raw)


def robj(redis: Redis,
         key: str | int,
         cl: Type[TBaseModel],
         throws: Optional[bool] = True) -> Optional[TBaseModel]:
    raw = redis.hgetall(key)
    logging.getLogger().debug(f"Raw HGETALL response: {raw}")
    if throws:
        return cl.parse_obj(none_throws(raw, key))

    return cl.parse_obj(raw) if raw is not None else None


def rkey(prefix: Key, *subscript: int | str) -> str:
    return f"{prefix}:{':'.join(subscript)}"


def trending_size(redis: Redis, throws: Optional[bool] = True) -> Optional[int]:
    return rint(redis, REDIS_TRENDING_SIZE_KEY, throws)
