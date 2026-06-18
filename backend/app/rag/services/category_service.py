import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.core.exceptions import NotFoundError, ValidationError
from app.rag.db import get_category_file_repository, get_category_repository
from app.rag.services.oss_service import get_oss_service

logger = logging.getLogger(__name__)

DEFAULT_CATEGORY_NAME = "__default__"


async def get_or_create_default_category(session: AsyncSession) -> dict:
    repo = get_category_repository(session)
    category = await repo.get_by_name(DEFAULT_CATEGORY_NAME)
    if not category:
        category = await repo.create(
            name=DEFAULT_CATEGORY_NAME,
            description="System default category for direct uploads",
        )
    return category


async def list_categories(session: AsyncSession) -> dict:
    categories = [
        item
        for item in await get_category_repository(session).list_all()
        if item["name"] != DEFAULT_CATEGORY_NAME
    ]
    return {"categories": categories, "total": len(categories)}


async def create_category(session: AsyncSession, name: str, description: str | None = None) -> dict:
    return await get_category_repository(session).create(name=name, description=description)


async def get_category_with_files(session: AsyncSession, category_id: str) -> dict:
    category = await get_category_repository(session).get(category_id)
    if not category:
        raise NotFoundError("Category not found")
    files = await get_category_file_repository(session).list_by_category(category_id)
    return {"category": category, "files": files, "file_count": len(files)}


async def update_category(
    session: AsyncSession,
    category_id: str,
    name: str | None,
    description: str | None,
) -> dict:
    repo = get_category_repository(session)
    if not await repo.get(category_id):
        raise NotFoundError("Category not found")
    await repo.update(category_id, name=name, description=description)
    return await repo.get(category_id)


async def delete_category(session: AsyncSession, category_id: str) -> None:
    category_repo = get_category_repository(session)
    category_file_repo = get_category_file_repository(session)
    category = await category_repo.get(category_id)
    if not category:
        raise NotFoundError("Category not found")
    if category["name"] == DEFAULT_CATEGORY_NAME:
        raise ValidationError("The system default category cannot be deleted")
    count = await category_file_repo.count_by_category(category_id)
    if count > 0:
        raise ValidationError(f"Delete the {count} files in this category first")
    await category_repo.delete(category_id)


async def delete_category_file(session: AsyncSession, category_id: str, file_id: str) -> str:
    category_file_repo = get_category_file_repository(session)
    record = await category_file_repo.get_by_id(file_id)
    if not record or record["category_id"] != category_id:
        raise NotFoundError("Category file not found")

    oss_key = record.get("oss_key")
    if oss_key:
        try:
            get_oss_service().delete_objects([oss_key])
        except Exception as exc:
            logger.warning("Failed to delete OSS object for category file", extra={"error": str(exc)})

    await category_file_repo.delete(file_id)
    return record["file_name"]


async def batch_delete_category_files(session: AsyncSession, category_id: str, file_ids: list[str]) -> dict:
    category_file_repo = get_category_file_repository(session)
    oss_keys: list[str] = []
    deleted: list[str] = []
    not_found: list[str] = []

    records = {}
    for file_id in file_ids:
        record = await category_file_repo.get_by_id(file_id)
        records[file_id] = record
        if not record or record["category_id"] != category_id:
            not_found.append(file_id)
            continue
        if record.get("oss_key"):
            oss_keys.append(record["oss_key"])
        deleted.append(record["file_name"])

    if oss_keys:
        try:
            get_oss_service().delete_objects(oss_keys)
        except Exception as exc:
            logger.warning("Failed to batch delete OSS category files", extra={"error": str(exc)})

    for file_id, record in records.items():
        if record and record["category_id"] == category_id:
            await category_file_repo.delete(file_id)

    return {"deleted": deleted, "not_found": not_found}
