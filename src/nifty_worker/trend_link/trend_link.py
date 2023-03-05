import logging
from typing import Any, Dict
from uuid import uuid1

from nifty_common import helpers
from nifty_common.types import Channel, TrendEvent, TrendLinkEvent, UpstreamSource
from nifty_worker.common.asyncio.worker import NiftyWorker


class TrendLinkWorker(NiftyWorker[TrendEvent]):

    def __init__(self):
        super().__init__()

    async def on_event(self, channel: Channel, msg: TrendEvent):
        r = self.redis()
        upstream = UpstreamSource(channel=channel, at=msg.at, uuid=msg.uuid)
        for c in [(a, True) for a in msg.added] + [(r, False) for r in msg.removed]:
            logging.debug('publishing evt')
            evt = TrendLinkEvent(uuid=str(uuid1()),
                                 at=helpers.timestamp_ms(),
                                 link_id=c[0],
                                 added=c[1],
                                 upstream=[upstream])
            await r.publish(Channel.trend_link, evt.json())

    async def on_yield(self): ...

    def unpack(self, msg: Dict[str, Any]) -> TrendEvent:
        return TrendEvent.parse_raw(msg['data'])
