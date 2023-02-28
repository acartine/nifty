import datetime
from dataclasses import dataclass
from enum import Enum
from typing import List, Set

from pydantic import BaseModel


@dataclass
class RedisType:
    cfg_key: str


class RedisConstants(RedisType, Enum):
    STD = RedisType("redis"),
    CACHE = RedisType("redis-cache")


class Key(str, Enum):
    long_url_by_short_url = 'nifty:long_url_by_short_url'


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
