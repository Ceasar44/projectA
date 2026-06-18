from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.flows.schemas import FlowCreate, FlowListResponse, FlowRead, FlowUpdate
from app.domain.flows.service import FlowService
from app.infrastructure.db.repositories.flows import FlowRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> FlowService:
    return FlowService(FlowRepository(session), SQLAlchemyUnitOfWork(session))


@router.get("", response_model=FlowListResponse)
async def list_flows(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None, alias="isActive"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> FlowListResponse:
    return await build_service(session).list_flows(page, limit, is_active)


@router.post("", response_model=FlowRead, status_code=status.HTTP_201_CREATED)
async def create_flow(
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> FlowRead:
    name = str(payload.get("name", "")).strip()
    if not name:
        return ORJSONResponse({"error": "Name is required"}, status_code=400)
    return await build_service(session).create_flow(FlowCreate.model_validate(payload))


@router.get("/{flow_id}", response_model=FlowRead)
async def get_flow(
    flow_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> FlowRead:
    return await build_service(session).get_flow(flow_id)


@router.put("/{flow_id}", response_model=FlowRead)
async def update_flow(
    flow_id: str,
    payload: FlowUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> FlowRead:
    return await build_service(session).update_flow(flow_id, payload)


@router.delete("/{flow_id}")
async def delete_flow(
    flow_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_flow(flow_id)


@router.post("/{flow_id}/validate")
async def validate_flow(
    flow_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await build_service(session).validate_flow(flow_id)
