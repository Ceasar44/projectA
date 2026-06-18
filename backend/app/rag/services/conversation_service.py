import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.core.exceptions import NotFoundError
from app.rag.db import get_conversation_repository

logger = logging.getLogger(__name__)


async def create_session(
    session: AsyncSession,
    kb_name: str,
    user_id: str = "default",
    title: str = "New conversation",
) -> dict:
    return await get_conversation_repository(session).create_session(
        kb_name=kb_name,
        user_id=user_id,
        title=title,
    )


async def list_sessions(session: AsyncSession, kb_name: str, user_id: str = "default") -> dict:
    rows = await get_conversation_repository(session).list_sessions(kb_name=kb_name, user_id=user_id)
    return {"sessions": rows, "total": len(rows)}


async def get_session_messages(session: AsyncSession, session_id: str, limit: int = 100) -> dict:
    repo = get_conversation_repository(session)
    conversation = await repo.get_session(session_id)
    if not conversation:
        raise NotFoundError(f"Conversation not found: {session_id}")
    messages = await repo.list_messages(session_id, limit=limit)
    return {"session": conversation, "messages": messages, "total": len(messages)}


async def delete_session(session: AsyncSession, session_id: str) -> None:
    repo = get_conversation_repository(session)
    conversation = await repo.get_session(session_id)
    if not conversation:
        raise NotFoundError(f"Conversation not found: {session_id}")

    try:
        messages = await repo.list_messages(session_id, limit=1000)
        oss_keys = [item["query_image_oss_key"] for item in messages if item.get("query_image_oss_key")]
        if oss_keys:
            from app.rag.services.oss_service import get_oss_service

            get_oss_service().delete_objects(oss_keys)
    except Exception as exc:
        logger.warning("Failed to clean conversation query images", extra={"error": str(exc)})

    await repo.delete_session(session_id)
