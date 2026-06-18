from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=300)
    phone: str | None = Field(default=None, max_length=50)
    whatsapp: str | None = Field(default=None, max_length=50)
    tags: str | None = Field(default=None, max_length=500)
    is_blocked: bool = Field(default=False, alias="isBlocked")


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=300)
    phone: str | None = Field(default=None, max_length=50)
    whatsapp: str | None = Field(default=None, max_length=50)
    tags: str | None = Field(default=None, max_length=500)
    is_blocked: bool | None = Field(default=None, alias="isBlocked")


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    email: str
    phone: str
    whatsapp: str
    tags: str
    is_blocked: bool = Field(alias="isBlocked")
    first_contact: datetime = Field(alias="firstContact")
    last_contact: datetime = Field(alias="lastContact")


class CustomerDetail(CustomerSummary):
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(PaginatedResponse[CustomerSummary]):
    pass
