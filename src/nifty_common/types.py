from enum import Enum

from pydantic import BaseModel


class Channel(str, Enum):
    action = 'action'
    hotlist_update = 'hotlistupdate'


class ActionType(str, Enum):
    get = 'get'
    create = 'create'


class Action(BaseModel):
    type: ActionType
    uuid: str
    at: int
    link_id: int
    short_url: str
    long_url: str
