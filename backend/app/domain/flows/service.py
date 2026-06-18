from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.flows.schemas import FlowCreate, FlowListResponse, FlowRead, FlowUpdate


class FlowService:
    def __init__(self, repo, uow):
        self.repo = repo
        self.uow = uow

    async def list_flows(self, page: int, limit: int, is_active: bool | None):
        items, total = await self.repo.list(page, limit, is_active)
        return FlowListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_flow(self, payload: FlowCreate) -> FlowRead:
        item = await self.repo.create(payload)
        await self.uow.commit()
        return FlowRead.model_validate(item)

    async def get_flow(self, flow_id: str) -> FlowRead:
        item = await self.repo.get(flow_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
        return FlowRead.model_validate(item)

    async def update_flow(self, flow_id: str, payload: FlowUpdate) -> FlowRead:
        item = await self.repo.update(flow_id, payload)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
        await self.uow.commit()
        return FlowRead.model_validate(item)

    async def delete_flow(self, flow_id: str) -> dict[str, bool]:
        deleted = await self.repo.delete(flow_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
        await self.uow.commit()
        return {"success": True}

    async def validate_flow(self, flow_id: str) -> dict[str, object]:
        return await self.repo.validate(flow_id)
