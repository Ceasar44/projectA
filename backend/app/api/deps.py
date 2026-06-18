from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import decode_access_token
from app.domain.auth.schemas import AuthContext
from app.domain.auth.service import AuthService
from app.domain.shared.enums import Role
from app.infrastructure.db.repositories.auth import AdminRepository, ApiKeyRepository


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


async def get_auth_context(
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_api_key: str | None = Header(default=None),
) -> AuthContext:
    service = AuthService(
        admin_repo=AdminRepository(session),
        api_key_repo=ApiKeyRepository(session),
    )
    if x_api_key:
        context = await service.authenticate_api_key(x_api_key)
        if context:
            return context
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    token = request.cookies.get("owly-token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    context = await service.load_user_context(payload.user_id)
    if not context:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return context


def require_role(*roles: Role):
    async def dependency(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if context.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return context

    return dependency
