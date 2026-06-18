from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class CampaignCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    channel: str = Field(default="email", max_length=50)
    message: str = Field(min_length=1)
    subject: str = Field(default="", max_length=500)
    segments: list[dict] = Field(default_factory=list)
    scheduled_at: datetime | None = Field(default=None, alias="scheduledAt")


class CampaignUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    channel: str | None = Field(default=None, max_length=50)
    message: str | None = None
    subject: str | None = Field(default=None, max_length=500)
    segments: list[dict] | None = None
    status: str | None = Field(default=None, max_length=50)
    scheduled_at: datetime | None = Field(default=None, alias="scheduledAt")


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    name: str
    description: str
    channel: str
    message: str
    subject: str
    segments: list[dict]
    status: str
    scheduled_at: datetime | None = Field(alias="scheduledAt")
    sent_count: int = Field(alias="sentCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class CampaignListResponse(PaginatedResponse[CampaignRead]):
    pass
