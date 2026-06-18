from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.compat import isoformat
from app.api.deps import get_session, require_role
from app.domain.admin.schemas import (
    AdminUserCreate,
    AdminUserRead,
    AdminUserUpdate,
    ApiKeyCreate,
    ApiKeyRead,
    ApiKeyUpdate,
)
from app.domain.admin.service import AdminService
from app.domain.auth.schemas import AuthContext
from app.domain.shared.enums import Role
from app.infrastructure.db.repositories.admin import AdminUserRepository, ManagedApiKeyRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> AdminService:
    return AdminService(
        AdminUserRepository(session),
        ManagedApiKeyRepository(session),
        SQLAlchemyUnitOfWork(session),
    )


@router.get("/users")
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    response = await build_service(session).list_users(page, limit)
    return [
        {
            "id": item.id,
            "username": item.username,
            "name": item.name,
            "role": item.role,
            "createdAt": isoformat(item.created_at),
            "updatedAt": isoformat(item.updated_at),
        }
        for item in response.data
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).create_user(payload)
    return {
        "id": item.id,
        "username": item.username,
        "name": item.name,
        "role": item.role,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).update_user(user_id, payload)
    return {
        "id": item.id,
        "username": item.username,
        "name": item.name,
        "role": item.role,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_user(user_id)


@router.get("/api-keys")
async def list_api_keys(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    response = await build_service(session).list_api_keys(page, limit)
    return [
        {
            "id": item.id,
            "name": item.name,
            "key": item.key,
            "isActive": item.is_active,
            "lastUsed": isoformat(item.last_used),
            "createdAt": isoformat(item.created_at),
            "updatedAt": isoformat(item.updated_at),
        }
        for item in response.data
    ]


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).create_api_key(payload)
    return {
        "id": item.id,
        "name": item.name,
        "key": item.key,
        "isActive": item.is_active,
        "lastUsed": isoformat(item.last_used),
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.put("/api-keys/{api_key_id}")
async def update_api_key(
    api_key_id: str,
    payload: ApiKeyUpdate,
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).update_api_key(api_key_id, payload)
    return {
        "id": item.id,
        "name": item.name,
        "key": item.key,
        "isActive": item.is_active,
        "lastUsed": isoformat(item.last_used),
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    _: AuthContext = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_api_key(api_key_id)


@router.get("/plugins")
async def list_plugins(_: AuthContext = Depends(require_role(Role.ADMIN))) -> list[dict[str, str]]:
    return []
