from fastapi import APIRouter, status

from app.api.v1 import (
    activity,
    admin,
    ai_workspace,
    analytics,
    auth,
    automation,
    business_hours,
    campaigns,
    canned_responses,
    channels,
    chat,
    conversations,
    customers,
    export,
    flows,
    health,
    knowledge,
    realtime,
    settings,
    sla,
    stats,
    team,
    tickets,
    tokens,
    webhooks,
)

try:
    from app.rag.api.v1 import router as rag_router
except ModuleNotFoundError as exc:
    rag_router = APIRouter(prefix="/v1")
    _rag_import_error = str(exc)

    @rag_router.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        include_in_schema=False,
    )
    async def rag_dependency_missing(path: str) -> dict[str, str]:
        return {
            "error": "RAG dependencies are not installed",
            "detail": _rag_import_error,
            "path": f"/rag/v1/{path}",
        }

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(ai_workspace.router, prefix="/knowledge/ai", tags=["knowledge-ai"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(business_hours.router, prefix="/business-hours", tags=["business-hours"])
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(flows.router, prefix="/flows", tags=["flows"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(team.router, prefix="/team", tags=["team"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["realtime"])
api_router.include_router(sla.router, prefix="/sla", tags=["sla"])
api_router.include_router(canned_responses.router, prefix="/canned-responses", tags=["canned-responses"])
api_router.include_router(activity.router, prefix="/activity", tags=["activity"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
