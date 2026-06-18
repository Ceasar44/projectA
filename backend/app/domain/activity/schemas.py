from datetime import datetime

from pydantic import BaseModel


class ActivityLogCreate(BaseModel):
    action: str
    entity: str
    entity_id: str | None = None
    description: str
    user_id: str | None = None
    user_name: str = "System"
    metadata: dict = {}


class ActivityLogRead(BaseModel):
    id: str
    action: str
    entity: str
    entity_id: str | None
    description: str
    user_id: str | None
    user_name: str
    metadata: dict
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    class Config:
        from_attributes = True
