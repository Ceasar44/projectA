from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.activity.service import ActivityService
from app.domain.auth.schemas import AuthContext

router = APIRouter()


def build_service(session: AsyncSession) -> ActivityService:
    return ActivityService(session)


@router.get("")
async def list_activities(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    entity: str | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    response = await build_service(session).list_activities(
        page, limit, None, entity, None, from_date, to_date
    )
    return {
        "data": [
            {
                **log.model_dump(),
                "createdAt": isoformat(log.created_at),
                "metadata": log.metadata,
            }
            for log in response.data
        ],
        "pagination": {
            "page": response.pagination.page,
            "limit": response.pagination.limit,
            "total": response.pagination.total,
            "totalPages": response.pagination.total_pages,
        },
    }
