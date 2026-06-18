from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse
from app.domain.shared.enums import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=10000)
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    conversation_id: str | None = Field(default=None, alias="conversationId")
    department_id: str | None = Field(default=None, alias="departmentId")
    assigned_to_id: str | None = Field(default=None, alias="assignedToId")


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    resolution: str | None = Field(default=None, max_length=10000)
    department_id: str | None = Field(default=None, alias="departmentId")
    assigned_to_id: str | None = Field(default=None, alias="assignedToId")


class TicketDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    description: str
    status: str
    priority: str
    resolution: str
    conversation_id: str | None = Field(alias="conversationId")
    department_id: str | None = Field(alias="departmentId")
    assigned_to_id: str | None = Field(alias="assignedToId")
    created_at: datetime
    updated_at: datetime


class TicketListResponse(PaginatedResponse[TicketDetail]):
    pass
