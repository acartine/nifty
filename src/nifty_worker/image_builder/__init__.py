import asyncio
import logging

from nifty_common.cfg import cfg
from nifty_common.types import Channel
from nifty_worker.common.worker import init_logger
from .enrichment import EnrichmentWorker

ENRICHMENT_CONFIG_KEY = "enrichment"

init_logger()
worker = EnrichmentWorker()
logging.getLogger(__name__).debug('launching asyncio')
asyncio.run(
    worker.run(
        src_channel=Channel.trend,
        listen_interval=cfg.getint(ENRICHMENT_CONFIG_KEY,
                                   'listen_interval_sec')))
