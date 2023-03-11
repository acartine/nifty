import asyncio
import logging

from nifty.common import cfg
from nifty.common.types import Channel
from nifty.common import log
from .image_builder import ImageBuilderWorker

ENRICHMENT_CONFIG_KEY = "enrichment"

log.log_init()
worker = ImageBuilderWorker()
logging.getLogger(__name__).debug("launching asyncio")
asyncio.run(
    worker.run(
        src_channel=Channel.trend,
        listen_interval=cfg.gint(ENRICHMENT_CONFIG_KEY, "listen_interval_sec"),
    )
)
