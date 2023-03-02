from datetime import datetime
from enum import Enum
from typing import Dict, List, Set

from pydantic import BaseModel

from nifty_common.helpers import timestamp_ms


class RedisType(Enum):
    STD = "redis",
    CACHE = "redis-cache"

    def __init__(self, cfg_key: str):
        self.cfg_key = cfg_key


class Key(str, Enum):
    link_id_cache = 'nifty:linkid:byshorturl'
    link_by_link_id = 'nifty:link:bylinkid'
    long_by_short = 'nifty:longurl:byshorturl'

    def sub(self, *subscript: str | int) -> str:
        return f"{self.value}:{'.'.join([str(s) for s in subscript])}"


class Channel(str, Enum):
    action = 'nifty:action'
    trend = 'nifty:trend'
    trend_link = 'nifty:trend:link'
    image_builder = 'nifty:trend:link:image'


class Link(BaseModel):
    id: int
    created_at: datetime
    long_url_id: int
    short_url_id: int
    long_url: str
    short_url: str

    def created_at_ms(self) -> int:
        return int(self.created_at.timestamp() * 1000)

    def redis_dict(self) -> Dict[str, int | str]:
        return {**self.dict(exclude={'created_at'}),
                'created_at': timestamp_ms(datetime_ts=self.created_at)}


class ActionType(str, Enum):
    get = 'get'
    create = 'create'


class Meta(BaseModel):
    uuid: str
    at: int


class UpstreamSource(Meta):
    channel: Channel


class DownstreamEvent(Meta):
    upstream: List[UpstreamSource]


class Action(Meta):
    type: ActionType
    link_id: int
    short_url: str
    long_url: str


class TrendEvent(Meta):
    added: Set[str]
    removed: Set[str]


class TrendLinkEvent(DownstreamEvent):
    short_url: str
    added: bool


class ImageEvent(DownstreamEvent):
    short_url: str
    image_key: str
