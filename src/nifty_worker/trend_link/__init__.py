import asyncio
import logging

from nifty_common import cfg
from nifty_common.types import Channel
from nifty_common import log
from .trend_link import TrendLinkWorker

TREND_LINK_CONFIG_KEY = "trend_link"

log.log_init()
worker = TrendLinkWorker()
logging.debug('launching asyncio')
asyncio.run(
    worker.run(
        src_channel=Channel.trend,
        listen_interval=cfg.getint(TREND_LINK_CONFIG_KEY,
                                   'listen_interval_sec')))
