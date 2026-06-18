from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class AutomationRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    type: str = Field(min_length=1, max_length=100)
    is_active: bool = Field(default=True, alias="isActive")
    conditions: list[dict] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0, le=1000)


class AutomationRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    type: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = Field(default=None, alias="isActive")
    conditions: list[dict] | None = None
    actions: list[dict] | None = None
    priority: int | None = Field(default=None, ge=0, le=1000)


class AutomationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    description: str
    type: str
    is_active: bool = Field(alias="isActive")
    conditions: list[dict]
    actions: list[dict]
    priority: int
    trigger_count: int = Field(alias="triggerCount")
    created_at: datetime
    updated_at: datetime


class AutomationRuleListResponse(PaginatedResponse[AutomationRuleRead]):
    pass
