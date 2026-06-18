from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, build_pagination
from app.domain.canned_responses.schemas import CannedResponseCreate, CannedResponseRead, CannedResponseUpdate
from app.infrastructure.db.models.operations import CannedResponse


class CannedResponseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_responses(
        self, page: int = 1, limit: int = 20, category: str | None = None, search: str | None = None
    ) -> PaginatedResponse[CannedResponseRead]:
        filters = []
        if category:
            filters.append(CannedResponse.category == category)
        if search:
            filters.append(
                CannedResponse.title.ilike(f"%{search}%") | CannedResponse.content.ilike(f"%{search}%")
            )

        total = await self.session.scalar(
            select(func.count()).select_from(CannedResponse).where(*filters)
        )

        responses = list(
            (
                await self.session.scalars(
                    select(CannedResponse)
                    .where(*filters)
                    .order_by(CannedResponse.usage_count.desc(), CannedResponse.created_at.desc())
                    .offset((page - 1) * limit)
                    .limit(limit)
                )
            ).all()
        )

        return PaginatedResponse(
            data=[CannedResponseRead.model_validate(r) for r in responses],
            pagination=build_pagination(page, limit, total or 0),
        )

    async def get_response(self, response_id: str) -> CannedResponseRead | None:
        response = await self.session.get(CannedResponse, response_id)
        return CannedResponseRead.model_validate(response) if response else None

    async def get_by_shortcut(self, shortcut: str) -> CannedResponseRead | None:
        response = await self.session.scalar(
            select(CannedResponse).where(
                CannedResponse.shortcut == shortcut, CannedResponse.is_active == True
            )
        )
        return CannedResponseRead.model_validate(response) if response else None

    async def create_response(self, payload: CannedResponseCreate) -> CannedResponseRead:
        response = CannedResponse(
            title=payload.title,
            content=payload.content,
            category=payload.category,
            shortcut=payload.shortcut,
            is_active=payload.is_active,
        )
        self.session.add(response)
        await self.session.commit()
        await self.session.refresh(response)
        return CannedResponseRead.model_validate(response)

    async def update_response(
        self, response_id: str, payload: CannedResponseUpdate
    ) -> CannedResponseRead | None:
        response = await self.session.get(CannedResponse, response_id)
        if not response:
            return None
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(response, key, value)
        await self.session.commit()
        await self.session.refresh(response)
        return CannedResponseRead.model_validate(response)

    async def delete_response(self, response_id: str) -> bool:
        response = await self.session.get(CannedResponse, response_id)
        if not response:
            return False
        await self.session.delete(response)
        await self.session.commit()
        return True

    async def increment_usage(self, response_id: str) -> bool:
        response = await self.session.get(CannedResponse, response_id)
        if not response:
            return False
        response.usage_count += 1
        await self.session.commit()
        return True

    async def list_categories(self) -> list[str]:
        results = await self.session.scalars(
            select(CannedResponse.category).distinct().order_by(CannedResponse.category)
        )
        return list(results.all())
