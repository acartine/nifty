from typing import Dict
from uuid import uuid1

from nifty_common.helpers import timestamp_ms
from nifty_common.types import Channel, TrendLinkEvent, EnrichmentEvent, UpstreamSource
from nifty_worker.common.async_worker import AsyncNiftyWorker


class EnrichmentWorker(AsyncNiftyWorker[TrendLinkEvent]):

    def __init__(self):
        super().__init__()

    async def on_event(self, channel: Channel, msg: TrendLinkEvent):
        r = self.redis()
        upstream = UpstreamSource(channel=channel, at=msg.at, uuid=msg.uuid)
        evt = EnrichmentEvent(uuid=str(uuid1()),
                              at=timestamp_ms(),
                              short_url=msg.short_url,
                              image_key="Foo",
                              upstream=[upstream] + msg.upstream)
        await r.publish(Channel.trend_link, evt.json())  # noqa

    async def on_yield(self): ...

    def unpack(self, msg: Dict[str, any]) -> TrendLinkEvent:
        return TrendLinkEvent.parse_raw(msg['data'])
