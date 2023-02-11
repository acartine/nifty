import logging

from redis.client import Redis

from nifty_common.helpers import retry


@retry(max_tries=3, stack_id=__name__)
def claim(redis: Redis, key: str | int, lifetime_sec: int) -> bool:
    with redis.pipeline() as pipe:
        pipe.watch(key)
        pipe.multi()
        res = pipe.incr(key).expire(key, lifetime_sec, nx=True).execute() # noqa
        logging.getLogger(__name__).debug(res)
        return int(res[0]) == 1
