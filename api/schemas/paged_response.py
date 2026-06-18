from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class PagedResponseHasNext(BaseModel, Generic[T]):
    has_next: bool
    after: str | None = None
    results: List[T]


class PagedResponseFull(BaseModel, Generic[T]):
    page: int
    total_pages: int
    total: int
    results: List[T]
