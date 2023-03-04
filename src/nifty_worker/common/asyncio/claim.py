import logging

from redis.asyncio.client import Redis

from nifty_common.asyncio import helpers


@helpers.retry(max_tries=3, stack_id=__name__)
async def claim(redis: Redis, key: str, lifetime_sec: int) -> bool:
    async with redis.pipeline() as pipe:
        await pipe.watch(key)
        pipe.multi()
        res = await (pipe.incr(key).expire(key, lifetime_sec, nx=True).execute())
        logging.getLogger(__name__).debug(res)
        return int(res[0]) == 1
