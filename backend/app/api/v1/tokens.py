from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.tokens.service import TokenService

router = APIRouter()


def parse_range_days(value: str) -> int:
    mapping = {"7d": 7, "30d": 30, "90d": 90}
    return mapping.get(value, 30)


@router.get("/overview")
async def token_overview(
    range_value: str = Query(default="30d", alias="range"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await TokenService(session).overview(parse_range_days(range_value))


@router.post("/recharge/orders")
async def create_recharge_order(
    payload: dict,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    package_name = str(payload.get("packageName", "")).strip()
    payment_method = str(payload.get("paymentMethod", "alipay")).strip() or "alipay"
    amount_cents = int(payload.get("amountCents", 0) or 0)
    tokens = int(payload.get("tokens", 0) or 0)
    if not package_name:
        return ORJSONResponse({"error": "packageName is required"}, status_code=400)
    if amount_cents <= 0 or tokens <= 0:
        return ORJSONResponse({"error": "amountCents and tokens must be greater than 0"}, status_code=400)

    order = await TokenService(session).create_recharge_order(
        package_name,
        payment_method,
        amount_cents,
        tokens,
        auth,
    )
    await session.commit()
    await session.refresh(order)
    return {
        "id": order.id,
        "packageName": order.package_name,
        "paymentMethod": order.payment_method,
        "amountCents": order.amount_cents,
        "tokens": order.tokens,
        "status": order.status,
        "createdAt": order.created_at.isoformat() if order.created_at else None,
    }


@router.post("/recharge/orders/{order_id}/complete")
async def complete_recharge_order(
    order_id: str,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    order = await TokenService(session).complete_recharge_order(order_id, auth)
    if not order:
        return ORJSONResponse({"error": "Recharge order not found"}, status_code=404)
    await session.commit()
    wallet = await TokenService(session).get_wallet()
    return {
        "id": order.id,
        "status": order.status,
        "completedAt": order.completed_at.isoformat() if order.completed_at else None,
        "remainingTokens": wallet.balance_tokens,
    }
