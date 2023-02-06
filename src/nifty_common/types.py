from enum import Enum

from pydantic import BaseModel


class Channel(str, Enum):
    action = 'action'


class ActionType(str, Enum):
    get = 'get'
    create = 'create'


class Action(BaseModel):
    type: ActionType
    at: int
    link_id: int
