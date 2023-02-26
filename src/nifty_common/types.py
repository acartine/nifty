from enum import Enum
from typing import List, Set

from pydantic import BaseModel


class Channel(str, Enum):
    action = 'action'
    trend = 'trend'
    trend_link = 'trend:link'
    enrichment = 'trend:link:enrichment'


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


class EnrichmentEvent(DownstreamEvent):
    short_urk: str
    image_key: str
