from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.business_hours.schemas import BusinessHoursRead, BusinessHoursUpdate
from app.domain.business_hours.service import BusinessHoursService
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> BusinessHoursService:
    return BusinessHoursService(SQLAlchemyUnitOfWork(session))


def serialize_business_hours(config: BusinessHoursRead) -> dict[str, object]:
    return config.model_dump(by_alias=True, mode="json")


@router.get("")
async def get_business_hours(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return serialize_business_hours(await build_service(session).get_config())


@router.put("")
async def update_business_hours(
    payload: BusinessHoursUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return serialize_business_hours(await build_service(session).update_config(payload))


@router.get("/check")
async def check_business_hours(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    is_within = await build_service(session).is_within_hours()
    return {"isWithinHours": is_within}
