from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.ai_workspace.service import AIWorkspaceService
from app.domain.auth.schemas import AuthContext

router = APIRouter()


@router.post("/outreach/generate")
async def generate_outreach(
    payload: dict,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    customer_id = str(payload.get("customerId", "")).strip()
    if not customer_id:
        return ORJSONResponse({"error": "customerId is required"}, status_code=400)
    knowledge_entry_ids = [str(item) for item in payload.get("knowledgeEntryIds", [])]
    channel = str(payload.get("channel", "email")).strip() or "email"
    purpose = str(payload.get("purpose", "")).strip()
    language = str(payload.get("language", "简体中文")).strip() or "简体中文"
    auto_delivery_enabled = bool(payload.get("autoDeliveryEnabled", False))
    result = await AIWorkspaceService(session).generate_outreach(
        customer_id,
        knowledge_entry_ids,
        channel,
        purpose,
        language,
        auto_delivery_enabled,
        auth,
    )
    if result.get("error"):
        return ORJSONResponse(result, status_code=404)
    return result


@router.post("/outreach/send")
async def send_outreach(
    payload: dict,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    draft_id = str(payload.get("draftId", "")).strip()
    subject = str(payload.get("subject", "")).strip()
    content = str(payload.get("content", "")).strip()
    channel = str(payload.get("channel", "email")).strip() or "email"
    auto_delivery_enabled = bool(payload.get("autoDeliveryEnabled", False))
    if not draft_id:
        return ORJSONResponse({"error": "draftId is required"}, status_code=400)
    if not content:
        return ORJSONResponse({"error": "content is required"}, status_code=400)
    result = await AIWorkspaceService(session).send_outreach(
        draft_id,
        channel,
        subject,
        content,
        auto_delivery_enabled,
        auth,
    )
    if result.get("error"):
        return ORJSONResponse(result, status_code=404)
    return result


@router.post("/intent/analyze")
async def analyze_intent(
    payload: dict,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    customer_id = str(payload.get("customerId", "")).strip()
    communication_goal = str(payload.get("communicationGoal", "")).strip()
    if not customer_id or not communication_goal:
        return ORJSONResponse(
            {"error": "customerId and communicationGoal are required"},
            status_code=400,
        )
    knowledge_entry_ids = [str(item) for item in payload.get("knowledgeEntryIds", [])]
    result = await AIWorkspaceService(session).analyze_intent(
        customer_id,
        communication_goal,
        knowledge_entry_ids,
        auth,
    )
    if result.get("error"):
        return ORJSONResponse(result, status_code=404)
    return result


@router.get("/customer-service/settings")
async def get_customer_service_settings(
    customer_id: str | None = Query(default=None, alias="customerId"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await AIWorkspaceService(session).get_customer_service_config(customer_id)


@router.put("/customer-service/settings")
async def update_customer_service_settings(
    payload: dict,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    scope = str(payload.get("scope", "global")).strip()
    if scope not in {"global", "customer"}:
        return ORJSONResponse({"error": "scope must be global or customer"}, status_code=400)
    if scope == "customer" and not str(payload.get("customerId", "")).strip():
        return ORJSONResponse({"error": "customerId is required for customer scope"}, status_code=400)
    return await AIWorkspaceService(session).upsert_customer_service_config(payload, auth)


@router.get("/customer-service/logs")
async def list_customer_service_logs(
    customer_id: str | None = Query(default=None, alias="customerId"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return {"data": await AIWorkspaceService(session).list_auto_reply_logs(customer_id)}


@router.get("/customer-service/customers")
async def list_customer_service_customers(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return {"data": await AIWorkspaceService(session).list_customer_service_customers()}
