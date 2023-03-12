from typing import List

from pydantic import BaseModel


class TrendingItem(BaseModel):
    id: int
    created_at: int
    long_url: str
    short_url: str
    views: int


class Trending(BaseModel):
    list: List[TrendingItem]


class Id(BaseModel):
    id: int | None = None


class Url(BaseModel):
    url: str | None = None


class UrlRow(BaseModel):
    id: int
    url: str
