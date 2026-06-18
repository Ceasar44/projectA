import secrets

from sqlalchemy import func, select

from app.domain.admin.schemas import AdminUserRead, ApiKeyRead
from app.infrastructure.db.models.auth import Admin, ApiKey


class AdminUserRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int):
        stmt = select(Admin).order_by(Admin.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(Admin)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [AdminUserRead.model_validate(row) for row in rows], total

    async def create(self, username: str, password: str, name: str, role: str) -> Admin:
        item = Admin(username=username, password=password, name=name, role=role)
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, user_id: str, name: str | None, role: str | None, password: str | None) -> Admin | None:
        item = await self.session.get(Admin, user_id)
        if not item:
            return None
        if name is not None:
            item.name = name
        if role is not None:
            item.role = role
        if password is not None:
            item.password = password
        await self.session.flush()
        return item

    async def delete(self, user_id: str) -> bool:
        item = await self.session.get(Admin, user_id)
        if not item:
            return False
        await self.session.delete(item)
        return True


class ManagedApiKeyRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int):
        stmt = select(ApiKey).order_by(ApiKey.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(ApiKey)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [ApiKeyRead.model_validate(row) for row in rows], total

    async def create(self, name: str) -> ApiKey:
        item = ApiKey(name=name, key=f"owly_{secrets.token_urlsafe(24)}")
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, api_key_id: str, name: str | None, is_active: bool | None) -> ApiKey | None:
        item = await self.session.get(ApiKey, api_key_id)
        if not item:
            return None
        if name is not None:
            item.name = name
        if is_active is not None:
            item.is_active = is_active
        await self.session.flush()
        return item

    async def delete(self, api_key_id: str) -> bool:
        item = await self.session.get(ApiKey, api_key_id)
        if not item:
            return False
        await self.session.delete(item)
        return True
