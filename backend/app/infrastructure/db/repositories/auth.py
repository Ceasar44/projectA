from datetime import UTC, datetime

from sqlalchemy import func, select, update

from app.infrastructure.db.models.auth import Admin, ApiKey


class AdminRepository:
    def __init__(self, session):
        self.session = session

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(Admin)) or 0

    async def add(self, admin: Admin) -> None:
        self.session.add(admin)
        await self.session.flush()

    async def get_by_username(self, username: str) -> Admin | None:
        return await self.session.scalar(select(Admin).where(Admin.username == username))

    async def get(self, admin_id: str) -> Admin | None:
        return await self.session.get(Admin, admin_id)


class ApiKeyRepository:
    def __init__(self, session):
        self.session = session

    async def get_active(self, raw_key: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.key == raw_key, ApiKey.is_active.is_(True))
        return await self.session.scalar(stmt)

    async def touch_last_used(self, api_key_id: str) -> None:
        await self.session.execute(
            update(ApiKey).where(ApiKey.id == api_key_id).values(last_used=datetime.now(UTC))
        )
