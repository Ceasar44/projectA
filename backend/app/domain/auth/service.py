from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.domain.auth.schemas import AuthContext, LoginRequest, SetupRequest
from app.domain.shared.enums import Role
from app.infrastructure.db.models.auth import Admin
from app.infrastructure.db.models.operations import Channel, Settings


class AuthService:
    def __init__(self, admin_repo, api_key_repo, settings_repo=None, uow=None):
        self.admin_repo = admin_repo
        self.api_key_repo = api_key_repo
        self.settings_repo = settings_repo
        self.uow = uow

    async def is_setup_complete(self) -> bool:
        return await self.admin_repo.count() > 0

    async def setup_admin(self, payload: SetupRequest) -> Admin:
        if await self.is_setup_complete():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Setup already completed")

        admin = Admin(
            username=payload.username,
            password=hash_password(payload.password),
            name=payload.name or "Admin",
            role=Role.ADMIN,
        )
        await self.admin_repo.add(admin)
        if self.settings_repo:
            await self.settings_repo.ensure_default(Settings())
            for channel_type in ("whatsapp", "email", "phone"):
                await self.settings_repo.ensure_channel(Channel(type=channel_type))
        if self.uow:
            await self.uow.commit()
        return admin

    async def login(self, payload: LoginRequest) -> Admin:
        admin = await self.admin_repo.get_by_username(payload.username)
        if not admin or not verify_password(payload.password, admin.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return admin

    async def authenticate_api_key(self, raw_key: str) -> AuthContext | None:
        api_key = await self.api_key_repo.get_active(raw_key)
        if not api_key:
            return None
        await self.api_key_repo.touch_last_used(api_key.id)
        return AuthContext(
            user_id=f"api-key:{api_key.id}",
            username=api_key.name,
            name=api_key.name,
            role=Role.ADMIN,
            auth_method="api_key",
        )

    async def load_user_context(self, user_id: str) -> AuthContext | None:
        admin = await self.admin_repo.get(user_id)
        if not admin:
            return None
        return AuthContext(
            user_id=admin.id,
            username=admin.username,
            name=admin.name,
            role=admin.role,
            auth_method="cookie",
        )
