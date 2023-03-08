# fixes stubs like redis that use generics when the code does not
from __future__ import annotations

import logging
from typing import Optional

from redis.asyncio.client import Redis

from nifty_common.asyncio import helpers
from nifty_worker.common.types import ClaimNamespace


@helpers.retry(max_tries=3, stack_id=__name__)
async def claim(
    redis: Redis[str],  # pyright: ignore [reportUnknownParameterType]
    claim_namespace: ClaimNamespace,
    key: str,
    *,
    lifetime_sec: Optional[int] = 60,
) -> bool:
    if lifetime_sec is None:
        raise Exception("lifetime_sec must be > 0")

    fqkey = f"nifty:claim:{claim_namespace.value}:{key}"
    async with redis.pipeline() as pipe:
        await pipe.watch(fqkey)
        pipe.multi()
        res = await pipe.incr(fqkey).expire(fqkey, lifetime_sec, nx=True).execute()
        logging.debug(res)
        return int(res[0]) == 1
