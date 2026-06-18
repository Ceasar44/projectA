from datetime import datetime

from sqlalchemy import func, select

from app.domain.campaigns.schemas import CampaignCreate, CampaignRead, CampaignUpdate
from app.infrastructure.db.models.operations import Campaign
from app.infrastructure.db.models.conversations import Customer


def _matches_segment(customer: Customer, segment: dict) -> bool:
    field = str(segment.get("field", ""))
    operator = str(segment.get("operator", ""))
    target = str(segment.get("value", "")).lower()
    raw_value = getattr(customer, field, "") or ""
    value = raw_value.isoformat() if isinstance(raw_value, datetime) else str(raw_value)
    lower = value.lower()

    if operator == "equals":
        return lower == target
    if operator == "contains":
        return target in lower
    if operator == "not_contains":
        return target not in lower
    if operator == "starts_with":
        return lower.startswith(target)
    if operator == "before":
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")) < datetime.fromisoformat(target.replace("Z", "+00:00"))
        except ValueError:
            return False
    if operator == "after":
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")) > datetime.fromisoformat(target.replace("Z", "+00:00"))
        except ValueError:
            return False
    if operator == "is_empty":
        return lower == ""
    if operator == "is_not_empty":
        return lower != ""
    return False


class CampaignRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int, status_value: str | None, channel: str | None):
        filters = []
        if status_value:
            filters.append(Campaign.status == status_value)
        if channel:
            filters.append(Campaign.channel == channel)
        stmt = select(Campaign).where(*filters).order_by(Campaign.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(Campaign).where(*filters)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [CampaignRead.model_validate(row) for row in rows], total

    async def create(self, payload: CampaignCreate) -> Campaign:
        item = Campaign(**payload.model_dump(by_alias=False))
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, campaign_id: str) -> Campaign | None:
        return await self.session.get(Campaign, campaign_id)

    async def update(self, campaign_id: str, payload: CampaignUpdate) -> Campaign | None:
        item = await self.get(campaign_id)
        if not item:
            return None
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def delete(self, campaign_id: str) -> bool:
        item = await self.get(campaign_id)
        if not item:
            return False
        await self.session.delete(item)
        return True

    async def execute(self, campaign_id: str) -> int:
        item = await self.get(campaign_id)
        if not item:
            return 0
        customers = list(
            (
                await self.session.scalars(
                    select(Customer)
                    .where(Customer.is_blocked == False)
                    .order_by(Customer.created_at.desc())
                    .limit(1000)
                )
            ).all()
        )
        segments = item.segments or []
        return len([customer for customer in customers if all(_matches_segment(customer, segment) for segment in segments)])
