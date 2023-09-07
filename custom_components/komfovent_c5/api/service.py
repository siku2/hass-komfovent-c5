from .client import Client


class Service:
    REG_CONTROLLER_FW_VERSION = 18003

    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    async def read_firmware_version(self) -> int:
        return await self._client.read_u16(self.REG_CONTROLLER_FW_VERSION)
