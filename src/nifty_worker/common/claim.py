import logging

from redis.client import Redis
from redis.asyncio.client import Redis as AsyncRedis
from nifty_common.helpers import async_retry, retry


# touch
@retry(max_tries=3, stack_id=__name__)
def claim(redis: Redis, key: str | int, lifetime_sec: int) -> bool:
    with redis.pipeline() as pipe:
        pipe.watch(key)
        pipe.multi()
        res = pipe.incr(key).expire(key, lifetime_sec, nx=True).execute()
        logging.getLogger(__name__).debug(res)
        return int(res[0]) == 1


@async_retry(max_tries=3, stack_id=__name__)
async def async_claim(redis: AsyncRedis, key: str | int, lifetime_sec: int) -> bool:
    async with redis.pipeline() as pipe:
        await pipe.watch(key)
        pipe.multi()
        res = await (pipe.incr(key).expire(key, lifetime_sec, nx=True).execute())
        logging.getLogger(__name__).debug(res)
        return int(res[0]) == 1
