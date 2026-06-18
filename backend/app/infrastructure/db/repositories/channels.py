from sqlalchemy import select

from app.domain.channels.schemas import ChannelConfigUpdate, ChannelRead
from app.infrastructure.db.models.operations import Channel


class ChannelRepository:
    CHANNEL_TYPES = ["whatsapp", "email", "phone", "sms", "telegram"]

    def __init__(self, session):
        self.session = session

    @staticmethod
    def _build_qr_data_uri(channel_type: str) -> str:
        svg = f"""
        <svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>
            <rect width='100%' height='100%' fill='white'/>
            <rect x='12' y='12' width='216' height='216' fill='none' stroke='#16a34a' stroke-width='4'/>
            <text x='50%' y='46%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='16' fill='#166534'>
                Scan to connect
            </text>
            <text x='50%' y='58%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='14' fill='#166534'>
                {channel_type.title()}
            </text>
        </svg>
        """.strip()
        return "data:image/svg+xml;utf8," + svg.replace("\n", "").replace("'", "%27").replace("#", "%23")

    async def list(self) -> list[ChannelRead]:
        rows = (await self.session.scalars(select(Channel).order_by(Channel.type.asc()))).all()
        by_type = {row.type: row for row in rows}
        result = []
        for channel_type in self.CHANNEL_TYPES:
            row = by_type.get(channel_type)
            if row:
                result.append(ChannelRead.model_validate(row))
            else:
                result.append(
                    ChannelRead(
                        id=None,
                        type=channel_type,
                        isActive=False,
                        config={},
                        status="disconnected",
                        created_at=None,
                        updated_at=None,
                    )
                )
        return result

    async def get(self, channel_type: str) -> ChannelRead:
        row = await self.session.scalar(select(Channel).where(Channel.type == channel_type))
        if not row:
            return ChannelRead(
                id=None,
                type=channel_type,
                isActive=False,
                config={},
                status="disconnected",
                created_at=None,
                updated_at=None,
            )
        return ChannelRead.model_validate(row)

    async def save(self, payload: ChannelConfigUpdate) -> ChannelRead:
        channel_type = payload.type or ""
        row = await self.session.scalar(select(Channel).where(Channel.type == channel_type))
        if not row:
            row = Channel(type=channel_type)
            self.session.add(row)
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            if field != "type":
                setattr(row, field, value)
        await self.session.flush()
        await self.session.refresh(row)
        return ChannelRead.model_validate(row)

    async def update(self, channel_type: str, payload: ChannelConfigUpdate) -> ChannelRead:
        row = await self.session.scalar(select(Channel).where(Channel.type == channel_type))
        if not row:
            row = Channel(type=channel_type)
            self.session.add(row)
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            if field != "type":
                setattr(row, field, value)
        await self.session.flush()
        await self.session.refresh(row)
        return ChannelRead.model_validate(row)

    async def perform_action(self, channel_type: str, action: str) -> dict:
        row = await self.session.scalar(select(Channel).where(Channel.type == channel_type))
        if not row:
            row = Channel(type=channel_type)
            self.session.add(row)
        config = dict(row.config or {})
        if action == "disconnect":
            row.status = "disconnected"
            row.is_active = False
            config.pop("qr", None)
        elif action == "connect":
            if channel_type == "whatsapp" and (config.get("mode") or "web") == "web":
                row.status = "pending"
                row.is_active = True
                config["qr"] = self._build_qr_data_uri(channel_type)
            else:
                row.status = "connected"
                row.is_active = True
        elif action == "test":
            if channel_type == "email":
                row.status = "connected" if config.get("smtpHost") else row.status
            elif channel_type == "phone":
                row.status = "connected" if config.get("twilioSid") else row.status
            elif channel_type == "whatsapp" and config.get("apiKey"):
                row.status = "connected"
        row.config = config
        await self.session.flush()
        return {
            "id": row.id,
            "type": row.type,
            "isActive": row.is_active,
            "config": row.config,
            "status": row.status,
            "message": f"{channel_type} action {action} completed",
            "qr": row.config.get("qr"),
        }
