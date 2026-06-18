from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.campaigns.schemas import CampaignCreate, CampaignListResponse, CampaignRead, CampaignUpdate
from app.domain.campaigns.service import CampaignService
from app.infrastructure.db.repositories.campaigns import CampaignRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> CampaignService:
    return CampaignService(CampaignRepository(session), SQLAlchemyUnitOfWork(session))


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_value: str | None = Query(default=None, alias="status"),
    channel: str | None = None,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CampaignListResponse:
    return await build_service(session).list_campaigns(page, limit, status_value, channel)


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CampaignRead:
    name = str(payload.get("name", "")).strip()
    message = str(payload.get("message", "")).strip()
    if not name:
        return ORJSONResponse({"error": "Name is required"}, status_code=400)
    if not message:
        return ORJSONResponse({"error": "Message is required"}, status_code=400)
    return await build_service(session).create_campaign(CampaignCreate.model_validate(payload))


@router.get("/{campaign_id}", response_model=CampaignRead)
async def get_campaign(
    campaign_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CampaignRead:
    return await build_service(session).get_campaign(campaign_id)


@router.put("/{campaign_id}", response_model=CampaignRead)
async def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CampaignRead:
    return await build_service(session).update_campaign(campaign_id, payload)


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_campaign(campaign_id)


@router.post("/{campaign_id}/execute")
async def execute_campaign(
    campaign_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await build_service(session).execute_campaign(campaign_id)
