from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PaginatedResponse


class FlowCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    start_node_id: str = Field(default="", alias="startNodeId", max_length=100)
    nodes: list[dict] = Field(default_factory=list)
    is_active: bool = Field(default=False, alias="isActive")


class FlowUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    start_node_id: str | None = Field(default=None, alias="startNodeId", max_length=100)
    nodes: list[dict] | None = None
    is_active: bool | None = Field(default=None, alias="isActive")


class FlowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str
    name: str
    description: str
    start_node_id: str = Field(alias="startNodeId")
    nodes: list[dict]
    is_active: bool = Field(alias="isActive")
    trigger_count: int = Field(alias="triggerCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class FlowListResponse(PaginatedResponse[FlowRead]):
    pass
