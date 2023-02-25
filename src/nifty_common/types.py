from enum import Enum
from typing import List, Set

from pydantic import BaseModel


class Channel(str, Enum):
    action = 'action'
    trending = 'trending'
    trending_link = 'trending:link'


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


class LinkTrendEvent(DownstreamEvent):
    short_url: str
    added: bool
