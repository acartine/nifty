from typing import Dict
from uuid import uuid1

from nifty_common.helpers import timestamp_ms
from nifty_common.types import Channel, TrendEvent, TrendLinkEvent, UpstreamSource
from nifty_worker.common.async_worker import AsyncNiftyWorker


class TrendLinkWorker(AsyncNiftyWorker[TrendEvent]):

    def __init__(self):
        super().__init__()

    async def on_event(self, channel: Channel, msg: TrendEvent):
        r = self.redis()
        upstream = UpstreamSource(channel=channel, at=msg.at, uuid=msg.uuid)
        for c in [(a, True) for a in msg.added] + [(r, False) for r in msg.removed]:
            evt = TrendLinkEvent(uuid=str(uuid1()),
                                 at=timestamp_ms(),
                                 short_url=c[0],
                                 added=c[1],
                                 upstream=[upstream])
            await r.publish(Channel.trend_link, evt.json())  # noqa

    async def on_yield(self): ...

    def unpack(self, msg: Dict[str, any]) -> TrendEvent:
        return TrendEvent.parse_raw(msg['data'])
