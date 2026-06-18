from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.services import conversation_service

router = APIRouter(prefix="/conversations", tags=["rag-conversations"])


class CreateSessionRequest(BaseModel):
    kb_name: str
    title: str = "New conversation"
    user_id: str = "default"


@router.get("")
async def list_sessions(
    kb_name: str = Query(...),
    user_id: str = Query(default="default"),
    session: AsyncSession = Depends(get_session),
):
    result = await conversation_service.list_sessions(session, kb_name=kb_name, user_id=user_id)
    return {"success": True, "data": result}


@router.post("")
async def create_session(body: CreateSessionRequest, session: AsyncSession = Depends(get_session)):
    conversation = await conversation_service.create_session(
        session,
        kb_name=body.kb_name,
        user_id=body.user_id,
        title=body.title,
    )
    await session.commit()
    return {"success": True, "data": conversation}


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    result = await conversation_service.get_session_messages(session, session_id, limit=limit)
    return {"success": True, "data": result}


@router.delete("/{session_id}")
async def delete_session(session_id: str, session: AsyncSession = Depends(get_session)):
    await conversation_service.delete_session(session, session_id)
    await session.commit()
    return {"success": True, "message": "Conversation deleted"}
