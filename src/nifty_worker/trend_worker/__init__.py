from nifty_common.config import cfg
from nifty_common.types import Channel
from .trend_worker import TrendWorker
from nifty_worker.common.worker import init_logger

init_logger()
TrendWorker().run(
    src_channel=Channel.action,
    listen_interval=cfg.getint(Channel.trend, 'listen_interval_sec'))
