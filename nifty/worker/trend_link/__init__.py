from nifty.common.types import Channel
from nifty.worker.common.asyncio import worker
from .trend_link import TrendLinkWorker

worker.start(lambda: TrendLinkWorker(), src_channel=Channel.trend_link)
