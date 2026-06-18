from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.operations.schemas import (
    BusinessHoursRead,
    BusinessHoursUpdate,
    CannedResponseCreate,
    CannedResponseListResponse,
    CannedResponseRead,
    CannedResponseUpdate,
    SLARuleCreate,
    SLARuleListResponse,
    SLARuleRead,
    SLARuleUpdate,
)


class OperationsService:
    def __init__(self, repo, uow):
        self.repo = repo
        self.uow = uow

    async def get_business_hours(self) -> BusinessHoursRead:
        return BusinessHoursRead.model_validate(await self.repo.get_business_hours())

    async def update_business_hours(self, payload: BusinessHoursUpdate) -> BusinessHoursRead:
        item = await self.repo.update_business_hours(payload)
        await self.uow.commit()
        return BusinessHoursRead.model_validate(item)

    async def list_sla(self, page: int, limit: int):
        items, total = await self.repo.list_sla(page, limit)
        return SLARuleListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_sla(self, payload: SLARuleCreate) -> SLARuleRead:
        item = await self.repo.create_sla(payload)
        await self.uow.commit()
        return SLARuleRead.model_validate(item)

    async def update_sla(self, rule_id: str, payload: SLARuleUpdate) -> SLARuleRead:
        item = await self.repo.update_sla(rule_id, payload)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA rule not found")
        await self.uow.commit()
        return SLARuleRead.model_validate(item)

    async def delete_sla(self, rule_id: str) -> dict[str, bool]:
        if not await self.repo.delete_sla(rule_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA rule not found")
        await self.uow.commit()
        return {"success": True}

    async def list_canned(self, page: int, limit: int):
        items, total = await self.repo.list_canned(page, limit)
        return CannedResponseListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_canned(self, payload: CannedResponseCreate) -> CannedResponseRead:
        item = await self.repo.create_canned(payload)
        await self.uow.commit()
        return CannedResponseRead.model_validate(item)

    async def update_canned(self, item_id: str, payload: CannedResponseUpdate) -> CannedResponseRead:
        item = await self.repo.update_canned(item_id, payload)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canned response not found")
        await self.uow.commit()
        return CannedResponseRead.model_validate(item)

    async def delete_canned(self, item_id: str) -> dict[str, bool]:
        if not await self.repo.delete_canned(item_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canned response not found")
        await self.uow.commit()
        return {"success": True}
