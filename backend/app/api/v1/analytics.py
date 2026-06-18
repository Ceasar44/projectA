from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.infrastructure.db.repositories.analytics import AnalyticsRepository

router = APIRouter()


@router.get("/stats")
async def stats(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await AnalyticsRepository(session).stats()


@router.get("/analytics")
async def analytics(
    period: str = Query(default="7d"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    result = await AnalyticsRepository(session).overview()
    result.setdefault("conversationsPerDay", [])
    result.setdefault("channelBreakdown", [])
    result.setdefault("avgResponseTime", 0)
    result.setdefault("resolutionRate", 0)
    result.setdefault("satisfactionAvg", 0)
    result.setdefault("ticketsByPriority", [])
    result.setdefault("ticketsByStatus", [])
    result.setdefault("topCategories", [])
    result.setdefault("teamPerformance", [])
    result.setdefault("totalConversations", sum(item["count"] for item in result["channelBreakdown"]))
    result["period"] = period
    return result


@router.get("/activity")
async def activity(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    entity: str | None = Query(default=None),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    rows, total = await AnalyticsRepository(session).activity(page, limit)
    if entity:
        rows = [row for row in rows if row.entity == entity]
        total = len(rows)
    return {
        "activities": [
            {
                "id": row.id,
                "action": row.action,
                "entity": row.entity,
                "entityId": row.entity_id,
                "description": row.description,
                "userName": row.user_name,
                "metadata": getattr(row, "metadata_json", {}) or {},
                "createdAt": isoformat(row.created_at),
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": max(1, (total + limit - 1) // limit),
    }
