from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=200)
    name: str = Field(default="Admin", max_length=200)
    role: str = Field(default="admin", max_length=20)


class AdminUserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=6, max_length=200)
    name: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=20)


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    name: str
    role: str
    created_at: datetime
    updated_at: datetime


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ApiKeyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = Field(default=None, alias="isActive")


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    name: str
    key: str
    is_active: bool = Field(alias="isActive")
    last_used: datetime | None = Field(alias="lastUsed")
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(PaginatedResponse[AdminUserRead]):
    pass


class ApiKeyListResponse(PaginatedResponse[ApiKeyRead]):
    pass
