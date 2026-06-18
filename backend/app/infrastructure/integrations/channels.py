from typing import Protocol


class ChannelAdapter(Protocol):
    async def receive(self, payload: dict) -> dict: ...
    async def send(self, payload: dict) -> dict: ...


class EmailChannelAdapter:
    async def receive(self, payload: dict) -> dict:
        return {"channel": "email", "status": "received", "payload": payload}

    async def send(self, payload: dict) -> dict:
        return {"channel": "email", "status": "sent", "payload": payload}


class PhoneChannelAdapter:
    async def receive(self, payload: dict) -> dict:
        return {"channel": "phone", "status": "received", "payload": payload}

    async def send(self, payload: dict) -> dict:
        return {"channel": "phone", "status": "sent", "payload": payload}


class WhatsAppChannelAdapter:
    async def receive(self, payload: dict) -> dict:
        return {"channel": "whatsapp", "status": "received", "payload": payload}

    async def send(self, payload: dict) -> dict:
        return {"channel": "whatsapp", "status": "sent", "payload": payload}
