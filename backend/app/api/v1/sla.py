from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.sla.schemas import SLACreate, SLARead, SLAUpdate
from app.domain.sla.service import SLAService
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> SLAService:
    return SLAService(SQLAlchemyUnitOfWork(session))


@router.get("")
async def list_sla_rules(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    response = await build_service(session).list_rules(page, limit)
    return {
        "data": [rule.model_dump(by_alias=True) for rule in response.data],
        "pagination": {
            "page": response.pagination.page,
            "limit": response.pagination.limit,
            "total": response.pagination.total,
            "totalPages": response.pagination.total_pages,
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SLARead)
async def create_sla_rule(
    payload: SLACreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> SLARead:
    return await build_service(session).create_rule(payload)


@router.get("/{rule_id}", response_model=SLARead)
async def get_sla_rule(
    rule_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> SLARead | None:
    return await build_service(session).get_rule(rule_id)


@router.put("/{rule_id}", response_model=SLARead)
async def update_sla_rule(
    rule_id: str,
    payload: SLAUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> SLARead | None:
    return await build_service(session).update_rule(rule_id, payload)


@router.delete("/{rule_id}")
async def delete_sla_rule(
    rule_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    success = await build_service(session).delete_rule(rule_id)
    return {"success": success}
