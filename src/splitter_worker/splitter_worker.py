from typing import Dict
from uuid import uuid1

from nifty_common.async_worker import AsyncNiftyWorker
from nifty_common.config import cfg
from nifty_common.helpers import timestamp_ms
from nifty_common.types import Channel, LinkTrendEvent, TrendEvent


class SplitterWorker(AsyncNiftyWorker[TrendEvent]):
    async def on_event(self, msg: TrendEvent):
        r = self.redis()
        for a in msg.added:
            evt = LinkTrendEvent(uuid=str(uuid1()),
                                 at=timestamp_ms(),
                                 short_url=a,
                                 added=True)
            await r.publish(Channel.trending_link, evt.json()) # noqa

    async def on_yield(self): ...

    def unpack(self, msg: Dict[str, any]) -> TrendEvent:
        return TrendEvent.parse_raw(msg['data'])


if __name__ == '__main__':
    SplitterWorker().run(
        src_channel=Channel.trending,
        listen_interval=cfg.getint('splitter', 'listen_interval_sec'))
