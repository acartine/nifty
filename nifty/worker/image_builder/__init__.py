from nifty.common.types import Channel
from nifty.worker.common.asyncio import worker
from .image_builder import ImageBuilderWorker

worker.start(lambda: ImageBuilderWorker(), src_channel=Channel.image_builder)
