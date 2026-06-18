from sqlalchemy import func, select

from app.domain.operations.schemas import (
    BusinessHoursUpdate,
    CannedResponseCreate,
    CannedResponseRead,
    CannedResponseUpdate,
    SLARuleCreate,
    SLARuleRead,
    SLARuleUpdate,
)
from app.infrastructure.db.models.operations import BusinessHours, CannedResponse, SLARule


class OperationsRepository:
    def __init__(self, session):
        self.session = session

    async def get_business_hours(self) -> BusinessHours:
        item = await self.session.get(BusinessHours, "default")
        if not item:
            item = BusinessHours()
            self.session.add(item)
            await self.session.flush()
        return item

    async def update_business_hours(self, payload: BusinessHoursUpdate) -> BusinessHours:
        item = await self.get_business_hours()
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def list_sla(self, page: int, limit: int):
        stmt = select(SLARule).order_by(SLARule.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(SLARule)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [SLARuleRead.model_validate(row) for row in rows], total

    async def create_sla(self, payload: SLARuleCreate) -> SLARule:
        item = SLARule(**payload.model_dump(by_alias=False))
        self.session.add(item)
        await self.session.flush()
        return item

    async def update_sla(self, rule_id: str, payload: SLARuleUpdate) -> SLARule | None:
        item = await self.session.get(SLARule, rule_id)
        if not item:
            return None
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def delete_sla(self, rule_id: str) -> bool:
        item = await self.session.get(SLARule, rule_id)
        if not item:
            return False
        await self.session.delete(item)
        return True

    async def list_canned(self, page: int, limit: int):
        stmt = select(CannedResponse).order_by(CannedResponse.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(CannedResponse)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [CannedResponseRead.model_validate(row) for row in rows], total

    async def create_canned(self, payload: CannedResponseCreate) -> CannedResponse:
        item = CannedResponse(**payload.model_dump(by_alias=False))
        self.session.add(item)
        await self.session.flush()
        return item

    async def update_canned(self, item_id: str, payload: CannedResponseUpdate) -> CannedResponse | None:
        item = await self.session.get(CannedResponse, item_id)
        if not item:
            return None
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def delete_canned(self, item_id: str) -> bool:
        item = await self.session.get(CannedResponse, item_id)
        if not item:
            return False
        await self.session.delete(item)
        return True
