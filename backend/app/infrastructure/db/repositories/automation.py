from sqlalchemy import func, select

from app.domain.automation.schemas import AutomationRuleCreate, AutomationRuleRead, AutomationRuleUpdate
from app.infrastructure.db.models.operations import AutomationRule


class AutomationRuleRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int, is_active: bool | None):
        filters = []
        if is_active is not None:
            filters.append(AutomationRule.is_active == is_active)
        stmt = select(AutomationRule).where(*filters).order_by(AutomationRule.priority.desc(), AutomationRule.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(AutomationRule).where(*filters)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [AutomationRuleRead.model_validate(row) for row in rows], total

    async def list_active(self) -> "list[AutomationRule]":
        stmt = select(AutomationRule).where(AutomationRule.is_active == True).order_by(AutomationRule.priority.desc(), AutomationRule.created_at.desc())
        return list((await self.session.scalars(stmt)).all())

    async def create(self, payload: AutomationRuleCreate) -> AutomationRule:
        item = AutomationRule(**payload.model_dump(by_alias=False))
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, rule_id: str, payload: AutomationRuleUpdate) -> AutomationRule | None:
        item = await self.session.get(AutomationRule, rule_id)
        if not item:
            return None
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def delete(self, rule_id: str) -> bool:
        item = await self.session.get(AutomationRule, rule_id)
        if not item:
            return False
        await self.session.delete(item)
        return True

    async def increment_trigger_count(self, rule_id: str) -> None:
        item = await self.session.get(AutomationRule, rule_id)
        if item:
            item.trigger_count += 1
            await self.session.flush()
