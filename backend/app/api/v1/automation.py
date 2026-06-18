from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.automation.schemas import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
)
from app.domain.automation.service import AutomationService
from app.infrastructure.db.repositories.automation import AutomationRuleRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> AutomationService:
    return AutomationService(AutomationRuleRepository(session), SQLAlchemyUnitOfWork(session))


@router.get("")
async def list_rules(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    is_active: bool | None = Query(default=None, alias="isActive"),
    type_value: str | None = Query(default=None, alias="type"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    response = await build_service(session).list_rules(page, limit, is_active)
    items = response.data
    if type_value:
        items = [item for item in items if item.type == type_value]
    return [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "type": item.type,
            "isActive": item.is_active,
            "conditions": item.conditions,
            "actions": item.actions,
            "priority": item.priority,
            "triggerCount": item.trigger_count,
            "createdAt": isoformat(item.created_at),
            "updatedAt": isoformat(item.updated_at),
        }
        for item in items
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: AutomationRuleCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).create_rule(payload)
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "type": item.type,
        "isActive": item.is_active,
        "conditions": item.conditions,
        "actions": item.actions,
        "priority": item.priority,
        "triggerCount": item.trigger_count,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.put("/{rule_id}")
async def update_rule(
    rule_id: str,
    payload: AutomationRuleUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).update_rule(rule_id, payload)
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "type": item.type,
        "isActive": item.is_active,
        "conditions": item.conditions,
        "actions": item.actions,
        "priority": item.priority,
        "triggerCount": item.trigger_count,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_rule(rule_id)
