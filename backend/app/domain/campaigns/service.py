from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.campaigns.schemas import CampaignCreate, CampaignListResponse, CampaignRead, CampaignUpdate


class CampaignService:
    def __init__(self, repo, uow):
        self.repo = repo
        self.uow = uow

    async def list_campaigns(self, page: int, limit: int, status_value: str | None, channel: str | None):
        items, total = await self.repo.list(page, limit, status_value, channel)
        return CampaignListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_campaign(self, payload: CampaignCreate) -> CampaignRead:
        item = await self.repo.create(payload)
        await self.uow.commit()
        return CampaignRead.model_validate(item)

    async def get_campaign(self, campaign_id: str) -> CampaignRead:
        item = await self.repo.get(campaign_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        return CampaignRead.model_validate(item)

    async def update_campaign(self, campaign_id: str, payload: CampaignUpdate) -> CampaignRead:
        item = await self.repo.update(campaign_id, payload)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        await self.uow.commit()
        return CampaignRead.model_validate(item)

    async def delete_campaign(self, campaign_id: str) -> dict[str, bool]:
        deleted = await self.repo.delete(campaign_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        await self.uow.commit()
        return {"success": True}

    async def execute_campaign(self, campaign_id: str) -> dict[str, object]:
        target_count = await self.repo.execute(campaign_id)
        return {"campaignId": campaign_id, "targetCount": target_count}
