from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChannelConfigUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str | None = Field(default=None, max_length=50)
    is_active: bool | None = Field(default=None, alias="isActive")
    config: dict | None = None
    status: str | None = Field(default=None, max_length=50)


class ChannelActionRequest(BaseModel):
    action: str


class ChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str | None
    type: str
    is_active: bool = Field(alias="isActive")
    config: dict
    status: str
    created_at: datetime | None = Field(alias="createdAt")
    updated_at: datetime | None = Field(alias="updatedAt")
