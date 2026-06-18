from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page: int
    limit: int
    total: int
    total_pages: int = Field(alias="totalPages")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: PaginationMeta


def build_pagination(page: int, limit: int, total: int) -> PaginationMeta:
    return PaginationMeta(page=page, limit=limit, total=total, total_pages=max(1, ceil(total / limit)))
