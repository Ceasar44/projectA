import logging

from app.rag.core.config import settings

logger = logging.getLogger(__name__)


async def init_rag_runtime() -> None:
    if not settings.auto_init:
        logger.info("RAG runtime auto initialization is disabled")
        return

    settings.validate_required_env()

    from app.rag.core.checkpointer import init_checkpointer

    await init_checkpointer()
    logger.info("RAG runtime initialized")


async def close_rag_runtime() -> None:
    from app.rag.core.checkpointer import close_checkpointer

    await close_checkpointer()
