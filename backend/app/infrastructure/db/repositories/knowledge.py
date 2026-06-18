from sqlalchemy import func, select

from app.domain.knowledge.schemas import CategoryCreate, CategoryRead, EntryCreate, EntryRead
from app.infrastructure.db.models.knowledge import Category, KnowledgeEntry


class CategoryRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int):
        stmt = select(Category).order_by(Category.sort_order.asc(), Category.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(Category)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [CategoryRead.model_validate(row) for row in rows], total

    async def create(self, payload: CategoryCreate) -> Category:
        category = Category(**payload.model_dump(by_alias=False))
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def update(self, category_id: str, payload: CategoryCreate) -> Category | None:
        category = await self.session.get(Category, category_id)
        if not category:
            return None
        for field, value in payload.model_dump(by_alias=False).items():
            setattr(category, field, value)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: str) -> bool:
        category = await self.session.get(Category, category_id)
        if not category:
            return False
        await self.session.delete(category)
        return True


class KnowledgeEntryRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int, category_id: str | None):
        filters = [KnowledgeEntry.category_id == category_id] if category_id else []
        stmt = select(KnowledgeEntry).where(*filters).order_by(KnowledgeEntry.priority.desc(), KnowledgeEntry.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(KnowledgeEntry).where(*filters)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [EntryRead.model_validate(row) for row in rows], total

    async def create(self, payload: EntryCreate) -> KnowledgeEntry:
        entry = KnowledgeEntry(**payload.model_dump(by_alias=False))
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def update(self, entry_id: str, payload: EntryCreate) -> KnowledgeEntry | None:
        entry = await self.session.get(KnowledgeEntry, entry_id)
        if not entry:
            return None
        for field, value in payload.model_dump(by_alias=False).items():
            setattr(entry, field, value)
        entry.version += 1
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def delete(self, entry_id: str) -> bool:
        entry = await self.session.get(KnowledgeEntry, entry_id)
        if not entry:
            return False
        await self.session.delete(entry)
        return True
