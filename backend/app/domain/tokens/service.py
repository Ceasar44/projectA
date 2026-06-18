from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.activity.schemas import ActivityLogCreate
from app.domain.activity.service import ActivityService
from app.infrastructure.db.models.operations import (
    TokenLedgerEntry,
    TokenRechargeOrder,
    TokenWallet,
)


class TokenService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.activity_service = ActivityService(session)

    async def get_wallet(self) -> TokenWallet:
        wallet = await self.session.get(TokenWallet, "default")
        if not wallet:
            wallet = TokenWallet(id="default", balance_tokens=20000)
            self.session.add(wallet)
            await self.session.flush()
        return wallet

    def estimate_tokens(self, *parts: str) -> int:
        char_count = sum(len(part or "") for part in parts)
        return max(1, char_count // 4)

    async def record_consumption(
        self,
        amount: int,
        source: str,
        description: str,
        metadata: dict | None = None,
        reference_id: str | None = None,
    ) -> TokenLedgerEntry:
        wallet = await self.get_wallet()
        consumed = max(0, amount)
        wallet.balance_tokens = max(0, wallet.balance_tokens - consumed)
        wallet.total_consumed_tokens += consumed

        entry = TokenLedgerEntry(
            kind="consume",
            source=source,
            amount=-consumed,
            balance_after=wallet.balance_tokens,
            description=description,
            reference_id=reference_id,
            metadata_json=metadata or {},
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def record_recharge(
        self,
        amount_tokens: int,
        source: str,
        description: str,
        metadata: dict | None = None,
        reference_id: str | None = None,
    ) -> TokenLedgerEntry:
        wallet = await self.get_wallet()
        added = max(0, amount_tokens)
        wallet.balance_tokens += added
        wallet.total_recharged_tokens += added

        entry = TokenLedgerEntry(
            kind="recharge",
            source=source,
            amount=added,
            balance_after=wallet.balance_tokens,
            description=description,
            reference_id=reference_id,
            metadata_json=metadata or {},
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def create_recharge_order(
        self,
        package_name: str,
        payment_method: str,
        amount_cents: int,
        tokens: int,
        auth_context,
    ) -> TokenRechargeOrder:
        order = TokenRechargeOrder(
            package_name=package_name,
            payment_method=payment_method,
            amount_cents=amount_cents,
            tokens=tokens,
            status="pending",
            created_by_user_id=auth_context.user_id,
            created_by_name=auth_context.name,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def complete_recharge_order(self, order_id: str, auth_context) -> TokenRechargeOrder | None:
        order = await self.session.get(TokenRechargeOrder, order_id)
        if not order:
            return None
        if order.status == "paid":
            return order

        order.status = "paid"
        order.completed_at = datetime.now(UTC)
        await self.record_recharge(
            order.tokens,
            "token_recharge",
            f"{order.payment_method.upper()} recharge completed",
            {
                "orderId": order.id,
                "packageName": order.package_name,
                "paymentMethod": order.payment_method,
                "amountCents": order.amount_cents,
                "tokens": order.tokens,
            },
            reference_id=order.id,
        )
        await self.session.flush()

        await self.activity_service.log_activity(
            ActivityLogCreate(
                action="token_recharged",
                entity="billing",
                entity_id=order.id,
                description=f"{auth_context.name} completed a {order.payment_method} recharge for {order.tokens} tokens.",
                user_id=auth_context.user_id,
                user_name=auth_context.name,
                metadata={
                    "orderId": order.id,
                    "tokens": order.tokens,
                    "amountCents": order.amount_cents,
                    "paymentMethod": order.payment_method,
                },
            )
        )
        return order

    async def overview(self, range_days: int) -> dict[str, object]:
        wallet = await self.get_wallet()
        since = datetime.now(UTC) - timedelta(days=range_days)
        rows = (
            await self.session.execute(
                select(
                    func.date(TokenLedgerEntry.created_at),
                    func.sum(TokenLedgerEntry.amount),
                )
                .where(TokenLedgerEntry.created_at >= since)
                .group_by(func.date(TokenLedgerEntry.created_at))
                .order_by(func.date(TokenLedgerEntry.created_at))
            )
        ).all()
        amount_by_date = {}
        for date_value, amount in rows:
            amount_by_date[str(date_value)] = int(amount or 0)

        usage_trend = []
        start_date = since.date()
        end_date = datetime.now(UTC).date()
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.isoformat()
            numeric = amount_by_date.get(date_key, 0)
            usage_trend.append(
                {
                    "date": date_key,
                    "consumed": abs(min(numeric, 0)),
                    "recharged": max(numeric, 0),
                    "net": numeric,
                }
            )
            current_date += timedelta(days=1)

        recent_recharges = list(
            (
                await self.session.scalars(
                    select(TokenRechargeOrder)
                    .order_by(TokenRechargeOrder.created_at.desc())
                    .limit(10)
                )
            ).all()
        )
        recent_ledger = list(
            (
                await self.session.scalars(
                    select(TokenLedgerEntry)
                    .order_by(TokenLedgerEntry.created_at.desc())
                    .limit(20)
                )
            ).all()
        )

        return {
            "wallet": {
                "remainingTokens": wallet.balance_tokens,
                "totalConsumedTokens": wallet.total_consumed_tokens,
                "totalRechargedTokens": wallet.total_recharged_tokens,
            },
            "usageTrend": usage_trend,
            "recentRecharges": [
                {
                    "id": row.id,
                    "packageName": row.package_name,
                    "paymentMethod": row.payment_method,
                    "amountCents": row.amount_cents,
                    "tokens": row.tokens,
                    "status": row.status,
                    "createdByName": row.created_by_name,
                    "completedAt": row.completed_at.isoformat() if row.completed_at else None,
                    "createdAt": row.created_at.isoformat() if row.created_at else None,
                }
                for row in recent_recharges
            ],
            "recentLedger": [
                {
                    "id": row.id,
                    "kind": row.kind,
                    "source": row.source,
                    "amount": row.amount,
                    "balanceAfter": row.balance_after,
                    "description": row.description,
                    "metadata": row.metadata_json or {},
                    "createdAt": row.created_at.isoformat() if row.created_at else None,
                }
                for row in recent_ledger
            ],
        }
