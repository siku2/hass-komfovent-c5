import asyncio
import os
import sys
from pathlib import Path

import pytest

CUSTOM_COMPONENTS_PATH = (Path(__file__) / "../../custom_components").resolve()
sys.path.append(str(CUSTOM_COMPONENTS_PATH))


from komfovent_c5.api import Client  # noqa: E402

_global_client_lock = asyncio.Lock()


@pytest.fixture
async def client() -> Client:
    async with _global_client_lock:
        yield await Client.connect(
            os.getenv("TEST_DEVICE_HOSTNAME"),
            int(os.getenv("TEST_DEVICE_PORT", 502)),
        )
