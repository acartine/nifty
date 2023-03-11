# fixes stubs like redis that use generics when the code does not
from __future__ import annotations

import logging

from redis.client import Redis

from nifty.common.helpers import retry


# touch
@retry(max_tries=3, stack_id=__name__)
def claim(
    redis: Redis[str],
    key: str,
    lifetime_sec: int,
) -> bool:
    with redis.pipeline() as pipe:
        pipe.watch(key)
        pipe.multi()
        res = pipe.incr(key).expire(key, lifetime_sec, nx=True).execute()
        logging.getLogger(__name__).debug(res)
        return int(res[0]) == 1
