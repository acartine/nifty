from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis.asyncio.client import Redis as AsyncRedis
from redis.client import Redis

from nifty_common.config import cfg
from nifty_common.constants import REDIS_TRENDING_SIZE_KEY
from nifty_common.helpers import none_throws, noneint_throws, optint_or_none
from nifty_common.types import Key, RedisType

TBaseModel = TypeVar('TBaseModel', bound=BaseModel)


def get_redis(redis_type: RedisType) -> Redis:
    return Redis(host=cfg[redis_type.cfg_key]['host'], username=cfg[redis_type.cfg_key]['user'],
                 password=cfg[redis_type.cfg_key]['pwd'])


def get_redis_async(redis_type: RedisType) -> AsyncRedis:
    return AsyncRedis(host=cfg[redis_type.cfg_key]['host'], username=cfg[redis_type.cfg_key]['user'],
                      password=cfg[redis_type.cfg_key]['pwd'])


def redis_int(redis: Redis, key: str, throws: Optional[bool] = True) -> Optional[int]:
    raw = redis.get(key)
    return noneint_throws(raw, key) if throws else optint_or_none(raw)


def redis_obj(redis: Redis,
              key: str | int,
              cl: Type[TBaseModel],
              throws: Optional[bool] = True) -> Optional[TBaseModel]:
    raw = redis.get(key)
    if throws:
        return cl.parse_obj(none_throws(raw, key))

    return cl.parse_obj(raw) if raw is not None else None


def redis_key(prefix: Key, *subscript: int | str) -> str:
    return f"{prefix}:{':'.join(subscript)}"


def trending_size(redis: Redis, throws: Optional[bool] = True) -> Optional[int]:
    return redis_int(redis, REDIS_TRENDING_SIZE_KEY, throws)
