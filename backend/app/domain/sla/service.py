from sqlalchemy import func, select

from app.core.pagination import PaginatedResponse, build_pagination
from app.domain.sla.schemas import SLACreate, SLARead, SLAUpdate
from app.infrastructure.db.models.operations import SLARule


class SLAService:
    def __init__(self, uow):
        self.uow = uow

    async def list_rules(self, page: int = 1, limit: int = 20) -> PaginatedResponse[SLARead]:
        total = await self.uow.session.scalar(select(func.count()).select_from(SLARule)) or 0
        rules = list(
            (
                await self.uow.session.scalars(
                    select(SLARule)
                    .order_by(SLARule.created_at.desc())
                    .offset((page - 1) * limit)
                    .limit(limit)
                )
            ).all()
        )
        return PaginatedResponse(
            data=[SLARead.model_validate(r) for r in rules],
            pagination=build_pagination(page, limit, total),
        )

    async def get_rule(self, rule_id: str) -> SLARead | None:
        rule = await self.uow.session.get(SLARule, rule_id)
        return SLARead.model_validate(rule) if rule else None

    async def create_rule(self, payload: SLACreate) -> SLARead:
        rule = SLARule(
            name=payload.name,
            description=payload.description,
            channel=payload.channel,
            priority=payload.priority,
            first_response_mins=payload.first_response_mins,
            resolution_mins=payload.resolution_mins,
            is_active=payload.is_active,
        )
        self.uow.session.add(rule)
        await self.uow.commit()
        await self.uow.session.refresh(rule)
        return SLARead.model_validate(rule)

    async def update_rule(self, rule_id: str, payload: SLAUpdate) -> SLARead | None:
        rule = await self.uow.session.get(SLARule, rule_id)
        if not rule:
            return None
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)
        await self.uow.commit()
        await self.uow.session.refresh(rule)
        return SLARead.model_validate(rule)

    async def delete_rule(self, rule_id: str) -> bool:
        rule = await self.uow.session.get(SLARule, rule_id)
        if not rule:
            return False
        await self.uow.session.delete(rule)
        await self.uow.commit()
        return True
