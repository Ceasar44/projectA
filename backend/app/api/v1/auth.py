from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.security import create_access_token, decode_access_token
from app.domain.auth.schemas import AuthStatusResponse, LoginRequest, SetupRequest, UserResponse
from app.domain.auth.service import AuthService
from app.infrastructure.db.repositories.auth import AdminRepository, ApiKeyRepository
from app.infrastructure.db.repositories.settings import SettingsRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


class AuthActionRequest(BaseModel):
    action: str
    username: str | None = None
    password: str | None = None
    name: str | None = None


def _cookie(token: str) -> dict[str, object]:
    return {
        "key": "owly-token",
        "value": token,
        "httponly": True,
        "secure": False,
        "samesite": "lax",
        "max_age": 60 * 60 * 24 * 7,
        "path": "/",
    }


@router.get("", response_model=AuthStatusResponse)
async def auth_status(request: Request, session: AsyncSession = Depends(get_session)) -> AuthStatusResponse:
    service = AuthService(
        admin_repo=AdminRepository(session),
        api_key_repo=ApiKeyRepository(session),
    )
    setup_required = not await service.is_setup_complete()
    token = request.cookies.get("owly-token")
    if not token:
        return AuthStatusResponse(authenticated=False, setup_required=setup_required, user=None)
    payload = decode_access_token(token)
    if not payload:
        return AuthStatusResponse(authenticated=False, setup_required=setup_required, user=None)
    context = await service.load_user_context(payload.user_id)
    if not context:
        return AuthStatusResponse(authenticated=False, setup_required=setup_required, user=None)
    return AuthStatusResponse(
        authenticated=True,
        setup_required=setup_required,
        user=UserResponse(id=context.user_id, username=context.username, name=context.name, role=context.role),
    )


@router.post("/setup")
async def setup(
    payload: SetupRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    uow = SQLAlchemyUnitOfWork(session)
    service = AuthService(
        admin_repo=AdminRepository(session),
        api_key_repo=ApiKeyRepository(session),
        settings_repo=SettingsRepository(session),
        uow=uow,
    )
    user = await service.setup_admin(payload)
    token = create_access_token(user.id, user.role)
    response.set_cookie(**_cookie(token))
    return {"success": True, "user": UserResponse.model_validate(user)}


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    service = AuthService(
        admin_repo=AdminRepository(session),
        api_key_repo=ApiKeyRepository(session),
    )
    user = await service.login(payload)
    token = create_access_token(user.id, user.role)
    response.set_cookie(**_cookie(token))
    return {"success": True, "user": UserResponse.model_validate(user)}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie("owly-token", path="/")
    return {"success": True}


@router.post("")
async def auth_action(
    payload: AuthActionRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    if payload.action == "setup":
        if not payload.username or not payload.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        return await setup(
            SetupRequest(username=payload.username, password=payload.password, name=payload.name),
            response,
            session,
        )
    if payload.action == "login":
        if not payload.username or not payload.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        return await login(
            LoginRequest(username=payload.username, password=payload.password),
            response,
            session,
        )
    if payload.action == "logout":
        return await logout(response)
    raise HTTPException(status_code=400, detail="Invalid action")
