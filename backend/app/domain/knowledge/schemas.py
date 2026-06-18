from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    icon: str = Field(default="folder", max_length=50)
    color: str = Field(default="#4A7C9B", max_length=20)
    sort_order: int = Field(default=0, alias="sortOrder", ge=0)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    description: str
    icon: str
    color: str
    sort_order: int = Field(alias="sortOrder")
    created_at: datetime
    updated_at: datetime


class EntryCreate(BaseModel):
    category_id: str = Field(alias="categoryId")
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=100000)
    priority: int = Field(default=0, ge=0, le=100)
    is_active: bool = Field(default=True, alias="isActive")


class EntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    category_id: str = Field(alias="categoryId")
    title: str
    content: str
    priority: int
    is_active: bool = Field(alias="isActive")
    version: int
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(PaginatedResponse[CategoryRead]):
    pass


class EntryListResponse(PaginatedResponse[EntryRead]):
    pass
