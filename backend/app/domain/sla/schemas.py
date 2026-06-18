from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SLACreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str = ""
    channel: str = "all"
    priority: str = "all"
    first_response_mins: int = Field(default=30, alias="firstResponseMins")
    resolution_mins: int = Field(default=480, alias="resolutionMins")
    is_active: bool = Field(default=True, alias="isActive")


class SLAUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    description: str | None = None
    channel: str | None = None
    priority: str | None = None
    first_response_mins: int | None = Field(default=None, alias="firstResponseMins")
    resolution_mins: int | None = Field(default=None, alias="resolutionMins")
    is_active: bool | None = Field(default=None, alias="isActive")


class SLARead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    description: str
    channel: str
    priority: str
    first_response_mins: int = Field(alias="firstResponseMins")
    resolution_mins: int = Field(alias="resolutionMins")
    is_active: bool = Field(alias="isActive")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
