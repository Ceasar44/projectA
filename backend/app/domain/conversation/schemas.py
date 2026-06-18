from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse
from app.domain.shared.enums import ConversationStatus


class MessageCreate(BaseModel):
    role: str = Field(default="assistant", max_length=50)
    content: str = Field(min_length=1, max_length=50000)
    media_type: str | None = Field(default=None, alias="mediaType", max_length=100)
    media_url: str | None = Field(default=None, alias="mediaUrl", max_length=2000)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    role: str
    content: str
    media_type: str | None = Field(alias="mediaType")
    media_url: str | None = Field(alias="mediaUrl")
    created_at: datetime


class ConversationCreate(BaseModel):
    channel: str = Field(min_length=1, max_length=50)
    customer_name: str | None = Field(default=None, alias="customerName", max_length=200)
    customer_contact: str | None = Field(default=None, alias="customerContact", max_length=500)
    status: ConversationStatus = ConversationStatus.ACTIVE


class ConversationUpdate(BaseModel):
    status: ConversationStatus | None = None
    satisfaction: int | None = Field(default=None, ge=1, le=5)
    summary: str | None = Field(default=None, max_length=5000)
    customer_name: str | None = Field(default=None, alias="customerName", max_length=200)


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    channel: str
    customer_name: str = Field(alias="customerName")
    customer_contact: str = Field(alias="customerContact")
    status: str
    satisfaction: int | None
    summary: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageRead] = []


class ConversationListResponse(PaginatedResponse[ConversationSummary]):
    pass
