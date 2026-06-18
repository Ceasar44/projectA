from app.domain.settings.schemas import SettingsRead, SettingsUpdate


class SettingsService:
    def __init__(self, settings_repo, uow=None):
        self.settings_repo = settings_repo
        self.uow = uow

    async def get_settings(self) -> SettingsRead:
        settings = await self.settings_repo.get_default()
        return SettingsRead.model_validate(self.settings_repo.mask_secrets(settings))

    async def update_settings(self, payload: SettingsUpdate) -> SettingsRead:
        settings = await self.settings_repo.update_default(payload)
        if self.uow:
            await self.uow.commit()
        return SettingsRead.model_validate(self.settings_repo.mask_secrets(settings))
