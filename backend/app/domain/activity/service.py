from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, build_pagination
from app.domain.activity.schemas import ActivityLogCreate, ActivityLogRead
from app.infrastructure.db.models.operations import ActivityLog


class ActivityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_activity(
        self,
        payload: ActivityLogCreate,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ActivityLogRead:
        log = ActivityLog(
            action=payload.action,
            entity=payload.entity,
            entity_id=payload.entity_id,
            description=payload.description,
            user_id=payload.user_id,
            user_name=payload.user_name,
            metadata_json=payload.metadata,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return ActivityLogRead.model_validate(log)

    async def list_activities(
        self,
        page: int = 1,
        limit: int = 20,
        action: str | None = None,
        entity: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> PaginatedResponse[ActivityLogRead]:
        filters = []
        if action:
            filters.append(ActivityLog.action == action)
        if entity:
            filters.append(ActivityLog.entity == entity)
        if user_id:
            filters.append(ActivityLog.user_id == user_id)
        if start_date:
            filters.append(ActivityLog.created_at >= start_date)
        if end_date:
            filters.append(ActivityLog.created_at <= end_date)

        total = await self.session.scalar(
            select(func.count()).select_from(ActivityLog).where(*filters)
        )

        logs = list(
            (
                await self.session.scalars(
                    select(ActivityLog)
                    .where(*filters)
                    .order_by(ActivityLog.created_at.desc())
                    .offset((page - 1) * limit)
                    .limit(limit)
                )
            ).all()
        )

        return PaginatedResponse(
            data=[ActivityLogRead.model_validate(log) for log in logs],
            pagination=build_pagination(page, limit, total or 0),
        )

    async def get_recent_activity_count(self, hours: int = 24) -> int:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return await self.session.scalar(
            select(func.count()).select_from(ActivityLog).where(ActivityLog.created_at >= cutoff)
        ) or 0

    async def get_activity_summary(self, hours: int = 24) -> dict:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        by_action = list(
            (
                await self.session.scalars(
                    select(ActivityLog.action, func.count(ActivityLog.id).label("count"))
                    .where(ActivityLog.created_at >= cutoff)
                    .group_by(ActivityLog.action)
                    .order_by(func.count(ActivityLog.id).desc())
                )
            ).all()
        )

        by_entity = list(
            (
                await self.session.scalars(
                    select(ActivityLog.entity, func.count(ActivityLog.id).label("count"))
                    .where(ActivityLog.created_at >= cutoff)
                    .group_by(ActivityLog.entity)
                    .order_by(func.count(ActivityLog.id).desc())
                )
            ).all()
        )

        return {
            "total": await self.get_recent_activity_count(hours),
            "byAction": [{"action": a, "count": c} for a, c in by_action],
            "byEntity": [{"entity": e, "count": c} for e, c in by_entity],
        }
