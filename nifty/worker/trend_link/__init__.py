import asyncio
import logging

from nifty.common import cfg
from nifty.common.types import Channel
from nifty.common import log
from .trend_link import TrendLinkWorker

TREND_LINK_CONFIG_KEY = "trend_link"

log.log_init()
worker = TrendLinkWorker()
logging.debug("launching asyncio")
asyncio.run(
    worker.run(
        src_channel=Channel.trend,
        listen_interval=cfg.gint(TREND_LINK_CONFIG_KEY, "listen_interval_sec"),
    )
)
