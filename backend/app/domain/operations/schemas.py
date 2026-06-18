from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class BusinessHoursRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    enabled: bool
    timezone: str
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str
    sunday: str
    offline_message: str = Field(alias="offlineMessage")


class BusinessHoursUpdate(BaseModel):
    enabled: bool | None = None
    timezone: str | None = None
    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None
    sunday: str | None = None
    offline_message: str | None = Field(default=None, alias="offlineMessage")


class SLARuleCreate(BaseModel):
    name: str
    description: str = ""
    channel: str = "all"
    priority: str = "all"
    first_response_mins: int = Field(alias="firstResponseMins")
    resolution_mins: int = Field(alias="resolutionMins")
    is_active: bool = Field(default=True, alias="isActive")


class SLARuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    channel: str | None = None
    priority: str | None = None
    first_response_mins: int | None = Field(default=None, alias="firstResponseMins")
    resolution_mins: int | None = Field(default=None, alias="resolutionMins")
    is_active: bool | None = Field(default=None, alias="isActive")


class SLARuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    name: str
    description: str
    channel: str
    priority: str
    first_response_mins: int = Field(alias="firstResponseMins")
    resolution_mins: int = Field(alias="resolutionMins")
    is_active: bool = Field(alias="isActive")
    created_at: datetime
    updated_at: datetime


class CannedResponseCreate(BaseModel):
    title: str
    content: str
    category: str = "General"
    shortcut: str = ""
    is_active: bool = Field(default=True, alias="isActive")


class CannedResponseUpdate(BaseModel):
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
    created_at: datetime
    updated_at: datetime


class SLARuleListResponse(PaginatedResponse[SLARuleRead]):
    pass


class CannedResponseListResponse(PaginatedResponse[CannedResponseRead]):
    pass
