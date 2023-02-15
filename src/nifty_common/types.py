from enum import Enum
from typing import Set

from pydantic import BaseModel


class Channel(str, Enum):
    action = 'action'
    trending = 'trending'


class ActionType(str, Enum):
    get = 'get'
    create = 'create'


class Meta(BaseModel):
    uuid: str
    at: int


class Action(Meta):
    type: ActionType
    link_id: int
    short_url: str
    long_url: str


class TrendEvent(Meta):
    added: Set[str]
    removed: Set[str]
