import pytest
from komfovent_c5.api import Client, Settings

pytestmark = pytest.mark.asyncio


async def test_read_all(client: Client):
    settings = Settings(client)

    state = await settings.read_all()
    assert state
