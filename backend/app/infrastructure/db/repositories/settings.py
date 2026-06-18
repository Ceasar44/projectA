from sqlalchemy.inspection import inspect
from sqlalchemy import select

from app.infrastructure.db.models.operations import Channel, Settings


class SettingsRepository:
    SECRET_FIELDS = {
        "ai_api_key",
        "smtp_pass",
        "imap_pass",
        "twilio_token",
        "whatsapp_api_key",
        "telegram_bot_token",
        "eleven_labs_key",
    }

    def __init__(self, session):
        self.session = session

    async def ensure_default(self, model: Settings) -> None:
        existing = await self.session.get(Settings, "default")
        if not existing:
            self.session.add(model)
            await self.session.flush()

    async def ensure_channel(self, model: Channel) -> None:
        existing = await self.session.scalar(select(Channel).where(Channel.type == model.type))
        if not existing:
            self.session.add(model)
            await self.session.flush()

    async def get_default(self) -> Settings:
        settings = await self.session.get(Settings, "default")
        if not settings:
            settings = Settings()
            self.session.add(settings)
            await self.session.flush()
            await self.session.refresh(settings)
        return settings

    async def update_default(self, payload) -> Settings:
        settings = await self.get_default()
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            if field in self.SECRET_FIELDS and isinstance(value, str) and value.startswith("****"):
                continue
            setattr(settings, field, value)
        await self.session.flush()
        await self.session.refresh(settings)
        return settings

    def mask_secrets(self, settings: Settings) -> dict[str, object]:
        data = {
            column.key: getattr(settings, column.key)
            for column in inspect(settings).mapper.column_attrs
        }
        for field_name in (
            "ai_api_key",
            "smtp_pass",
            "imap_pass",
            "twilio_token",
            "whatsapp_api_key",
            "telegram_bot_token",
            "eleven_labs_key",
        ):
            value = data.get(field_name, "")
            if value:
                data[field_name] = "*" * 4 + str(value)[-4:]
        return data
