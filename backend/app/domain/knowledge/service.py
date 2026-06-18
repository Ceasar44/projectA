from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.knowledge.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryRead,
    EntryCreate,
    EntryListResponse,
    EntryRead,
)


class KnowledgeService:
    def __init__(self, category_repo, entry_repo, uow):
        self.category_repo = category_repo
        self.entry_repo = entry_repo
        self.uow = uow

    async def list_categories(self, page: int, limit: int):
        items, total = await self.category_repo.list(page, limit)
        return CategoryListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_category(self, payload: CategoryCreate) -> CategoryRead:
        category = await self.category_repo.create(payload)
        await self.uow.commit()
        return CategoryRead.model_validate(category)

    async def update_category(self, category_id: str, payload: CategoryCreate) -> CategoryRead:
        category = await self.category_repo.update(category_id, payload)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await self.uow.commit()
        return CategoryRead.model_validate(category)

    async def delete_category(self, category_id: str) -> dict[str, bool]:
        if not await self.category_repo.delete(category_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await self.uow.commit()
        return {"success": True}

    async def list_entries(self, page: int, limit: int, category_id: str | None):
        items, total = await self.entry_repo.list(page, limit, category_id)
        return EntryListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_entry(self, payload: EntryCreate) -> EntryRead:
        entry = await self.entry_repo.create(payload)
        await self.uow.commit()
        return EntryRead.model_validate(entry)

    async def update_entry(self, entry_id: str, payload: EntryCreate) -> EntryRead:
        entry = await self.entry_repo.update(entry_id, payload)
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
        await self.uow.commit()
        return EntryRead.model_validate(entry)

    async def delete_entry(self, entry_id: str) -> dict[str, bool]:
        if not await self.entry_repo.delete(entry_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
        await self.uow.commit()
        return {"success": True}

    async def test_knowledge(self, question: str) -> dict[str, object]:
        items, _ = await self.entry_repo.list(1, 20, None)
        answer = "No knowledge entries available."
        sources: list[dict[str, str]] = []
        if items:
            top = items[0]
            answer = f"Suggested answer based on '{top.title}': {top.content[:200]}"
            sources = [{"title": top.title, "category": top.category_id}]
        return {"question": question, "answer": answer, "sources": sources}
