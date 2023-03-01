import asyncio
import logging

from nifty_common.config import cfg
from nifty_common.types import Channel
from nifty_worker.common.worker import init_logger
from .trend_link import TrendLinkWorker

TREND_LINK_CONFIG_KEY = "trend_link"

init_logger()
worker = TrendLinkWorker()
logging.getLogger(__name__).debug('launching asyncio')
asyncio.run(
    worker.run(
        src_channel=Channel.trend,
        listen_interval=cfg.getint(TREND_LINK_CONFIG_KEY,
                                   'listen_interval_sec')))