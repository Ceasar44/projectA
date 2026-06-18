from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CannedResponseCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    content: str
    category: str = "General"
    shortcut: str = ""
    is_active: bool = Field(default=True, alias="isActive")


class CannedResponseUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    content: str | None = None
    category: str | None = None
    shortcut: str | None = None
    is_active: bool | None = Field(default=None, alias="isActive")


class CannedResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    content: str
    category: str
    shortcut: str
    is_active: bool = Field(alias="isActive")
    usage_count: int = Field(alias="usageCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
