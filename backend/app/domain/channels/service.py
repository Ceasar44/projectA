from app.domain.channels.schemas import ChannelConfigUpdate, ChannelRead


class ChannelService:
    def __init__(self, repo, uow):
        self.repo = repo
        self.uow = uow

    async def list_channels(self) -> list[ChannelRead]:
        return await self.repo.list()

    async def get_channel(self, channel_type: str) -> ChannelRead:
        return await self.repo.get(channel_type)

    async def save_channel(self, payload: ChannelConfigUpdate) -> ChannelRead:
        channel = await self.repo.save(payload)
        await self.uow.commit()
        return channel

    async def update_channel(self, channel_type: str, payload: ChannelConfigUpdate) -> ChannelRead:
        channel = await self.repo.update(channel_type, payload)
        await self.uow.commit()
        return channel

    async def perform_action(self, channel_type: str, action: str) -> dict:
        result = await self.repo.perform_action(channel_type, action)
        await self.uow.commit()
        return result
