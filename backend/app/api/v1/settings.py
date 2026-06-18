from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_role
from app.domain.auth.schemas import AuthContext
from app.domain.settings.schemas import SettingsRead, SettingsUpdate
from app.domain.settings.service import SettingsService
from app.domain.shared.enums import Role
from app.infrastructure.db.repositories.settings import SettingsRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


@router.get("", response_model=SettingsRead)
async def get_settings(
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> SettingsRead:
    service = SettingsService(SettingsRepository(session))
    return await service.get_settings()


@router.put("", response_model=SettingsRead)
async def update_settings(
    payload: SettingsUpdate,
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> SettingsRead:
    service = SettingsService(SettingsRepository(session), SQLAlchemyUnitOfWork(session))
    return await service.update_settings(payload)
