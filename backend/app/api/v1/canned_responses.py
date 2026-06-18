from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.canned_responses.schemas import CannedResponseCreate, CannedResponseRead, CannedResponseUpdate
from app.domain.canned_responses.service import CannedResponseService

router = APIRouter()


def build_service(session: AsyncSession) -> CannedResponseService:
    return CannedResponseService(session)


def serialize_canned_response(item: CannedResponseRead) -> dict[str, object]:
    return item.model_dump(by_alias=True, mode="json")


@router.get("")
async def list_canned_responses(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    search: str | None = None,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    response = await build_service(session).list_responses(page, limit, category, search)
    return {
        "data": [serialize_canned_response(r) for r in response.data],
        "pagination": {
            "page": response.pagination.page,
            "limit": response.pagination.limit,
            "total": response.pagination.total,
            "totalPages": response.pagination.total_pages,
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CannedResponseRead)
async def create_canned_response(
    payload: CannedResponseCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CannedResponseRead:
    return await build_service(session).create_response(payload)


@router.get("/categories")
async def list_categories(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[str]:
    return await build_service(session).list_categories()


@router.get("/shortcut/{shortcut}", response_model=CannedResponseRead)
async def get_by_shortcut(
    shortcut: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CannedResponseRead | None:
    return await build_service(session).get_by_shortcut(shortcut)


@router.get("/{response_id}", response_model=CannedResponseRead)
async def get_canned_response(
    response_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CannedResponseRead | None:
    return await build_service(session).get_response(response_id)


@router.put("/{response_id}", response_model=CannedResponseRead)
async def update_canned_response(
    response_id: str,
    payload: CannedResponseUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CannedResponseRead | None:
    return await build_service(session).update_response(response_id, payload)


@router.delete("/{response_id}")
async def delete_canned_response(
    response_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    success = await build_service(session).delete_response(response_id)
    return {"success": success}


@router.post("/{response_id}/use")
async def use_canned_response(
    response_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    success = await build_service(session).increment_usage(response_id)
    return {"success": success}
