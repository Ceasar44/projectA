from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.core.security import hash_password
from app.domain.admin.schemas import (
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserRead,
    AdminUserUpdate,
    ApiKeyCreate,
    ApiKeyListResponse,
    ApiKeyRead,
    ApiKeyUpdate,
)


class AdminService:
    def __init__(self, repo, api_key_repo, uow):
        self.repo = repo
        self.api_key_repo = api_key_repo
        self.uow = uow

    async def list_users(self, page: int, limit: int):
        items, total = await self.repo.list(page, limit)
        return AdminUserListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_user(self, payload: AdminUserCreate) -> AdminUserRead:
        item = await self.repo.create(payload.username, hash_password(payload.password), payload.name, payload.role)
        await self.uow.commit()
        return AdminUserRead.model_validate(item)

    async def update_user(self, user_id: str, payload: AdminUserUpdate) -> AdminUserRead:
        password = hash_password(payload.password) if payload.password else None
        item = await self.repo.update(user_id, payload.name, payload.role, password)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")
        await self.uow.commit()
        return AdminUserRead.model_validate(item)

    async def delete_user(self, user_id: str) -> dict[str, bool]:
        deleted = await self.repo.delete(user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")
        await self.uow.commit()
        return {"success": True}

    async def list_api_keys(self, page: int, limit: int):
        items, total = await self.api_key_repo.list(page, limit)
        return ApiKeyListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_api_key(self, payload: ApiKeyCreate) -> ApiKeyRead:
        item = await self.api_key_repo.create(payload.name)
        await self.uow.commit()
        return ApiKeyRead.model_validate(item)

    async def update_api_key(self, api_key_id: str, payload: ApiKeyUpdate) -> ApiKeyRead:
        item = await self.api_key_repo.update(api_key_id, payload.name, payload.is_active)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        await self.uow.commit()
        return ApiKeyRead.model_validate(item)

    async def delete_api_key(self, api_key_id: str) -> dict[str, bool]:
        deleted = await self.api_key_repo.delete(api_key_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        await self.uow.commit()
        return {"success": True}
