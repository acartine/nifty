from typing import Any, Dict

# from uuid import uuid1
# import io
# from PIL import Image
# from selenium import webdriver
# from nifty_common.helpers import timestamp_ms
from nifty_common.types import Channel, TrendLinkEvent
from nifty_worker.common.asyncio.worker import NiftyWorker
from nifty_worker.common.types import ClaimNamespace


class ImageBuilderWorker(NiftyWorker[TrendLinkEvent]):
    def __init__(self):
        super().__init__(ClaimNamespace.image)

    async def on_event(self, channel: Channel, msg: TrendLinkEvent):
        pass
        # r = self.redis()
        # options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')

        # driver = webdriver.Chrome(options=options)
        # driver.set_window_size(1920, 1080)
        # driver.get(msg.short_url)
        # screenshot = driver.get_screenshot_as_png()
        # driver.quit()

        # # Convert the screenshot from bytes to PIL Image object
        # image = Image.open(io.BytesIO(screenshot))

        # # Resize the image to 200x200 pixels
        # image = image.resize((200, 200))

        # # Save the image to a BytesIO buffer
        # buffer = io.BytesIO()
        # image.save(buffer, format='PNG')
        # image_bytes = buffer.getvalue()

        # # Save the image bytes to Redis
        # r.set(f"nifty:link:{msg.short_url}", image_bytes)
        # upstream = UpstreamSource(channel=channel, at=msg.at, uuid=msg.uuid)
        # evt = ImageEvent(uuid=str(uuid1()),
        #                  at=timestamp_ms(),
        #                  short_url=msg.short_url,
        #                  image_key="Foo",
        #                  upstream=[upstream] + msg.upstream)
        # await r.publish(Channel.trend_link, evt.json())  # noqa/

    async def on_yield(self):
        ...

    def unpack(self, msg: Dict[str, Any]) -> TrendLinkEvent:
        return TrendLinkEvent.parse_raw(msg["data"])
