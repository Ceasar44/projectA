from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class WebhookCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    url: str = Field(min_length=1, max_length=2000)
    method: str = Field(default="POST", max_length=10)
    headers: dict = Field(default_factory=dict)
    is_active: bool = Field(default=True, alias="isActive")
    trigger_on: str = Field(alias="triggerOn", min_length=1, max_length=200)


class WebhookUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    url: str | None = Field(default=None, min_length=1, max_length=2000)
    method: str | None = Field(default=None, max_length=10)
    headers: dict | None = None
    is_active: bool | None = Field(default=None, alias="isActive")
    trigger_on: str | None = Field(default=None, alias="triggerOn", min_length=1, max_length=200)


class WebhookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    name: str
    description: str
    url: str
    method: str
    headers: dict
    is_active: bool = Field(alias="isActive")
    trigger_on: str = Field(alias="triggerOn")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class WebhookDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    webhook_id: str = Field(alias="webhookId")
    event: str
    payload: dict
    status: str
    status_code: int | None = Field(alias="statusCode")
    attempts: int
    last_error: str | None = Field(alias="lastError")
    next_retry_at: datetime | None = Field(alias="nextRetryAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class WebhookListResponse(PaginatedResponse[WebhookRead]):
    pass


class WebhookDeliveryListResponse(PaginatedResponse[WebhookDeliveryRead]):
    pass
