"""Session helpers for RAG code paths.

Most RAG database access should receive an AsyncSession from FastAPI or service
code. A few legacy RAG/LangGraph/Milvus hooks are synchronous, so this module
provides a narrow bridge that still uses the main SQLAlchemy session factory.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal

T = TypeVar("T")


async def run_with_session(coro_fn: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async with SessionLocal() as session:
        return await coro_fn(session)


def run_with_session_sync(coro_fn: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Run an async DB operation from synchronous RAG code.

    The operation is executed in a short-lived thread with its own event loop so
    callers are safe whether or not the current thread already has a running
    asyncio loop.
    """

    result: dict[str, T] = {}
    error: dict[str, BaseException] = {}

    def _target() -> None:
        try:
            result["value"] = asyncio.run(run_with_session(coro_fn))
        except BaseException as exc:  # noqa: BLE001 - re-raise in caller thread
            error["error"] = exc

    thread = threading.Thread(target=_target, name="rag-db-sync", daemon=True)
    thread.start()
    thread.join()

    if error:
        raise error["error"]
    return result["value"]
