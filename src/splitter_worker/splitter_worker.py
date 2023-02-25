import asyncio
import logging
from typing import Dict
from uuid import uuid1

from nifty_common.async_worker import AsyncNiftyWorker
from nifty_common.config import cfg
from nifty_common.helpers import timestamp_ms
from nifty_common.types import Channel, LinkTrendEvent, TrendEvent, UpstreamSource
from nifty_common.worker import init_logger

init_logger()


class SplitterWorker(AsyncNiftyWorker[TrendEvent]):

    def __init__(self):
        super().__init__()

    async def on_event(self, channel: Channel, msg: TrendEvent):
        r = self.redis()
        upstream = UpstreamSource(channel=channel, at=msg.at, uuid=msg.uuid)
        for c in [(a, True) for a in msg.added] + [(r, False) for r in msg.removed]:
            evt = LinkTrendEvent(uuid=str(uuid1()),
                                 at=timestamp_ms(),
                                 short_url=c[0],
                                 added=c[1],
                                 upstream=[upstream])
            await r.publish(Channel.trending_link, evt.json())  # noqa

    async def on_yield(self): ...

    def unpack(self, msg: Dict[str, any]) -> TrendEvent:
        return TrendEvent.parse_raw(msg['data'])


if __name__ == '__main__':
    worker = SplitterWorker()
    logging.getLogger(__name__).debug('launching asyncio')
    asyncio.run(
        worker.run(
            src_channel=Channel.trending,
            listen_interval=cfg.getint('splitter', 'listen_interval_sec')))
