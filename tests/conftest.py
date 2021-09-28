import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import pytest

CUSTOM_COMPONENTS_PATH = (Path(__file__) / "../../custom_components").resolve()
sys.path.append(str(CUSTOM_COMPONENTS_PATH))


from komfovent_c5.api import Client

_global_client: Optional[Client] = None
_global_client_lock = asyncio.Lock()


@pytest.fixture
async def client() -> Client:
    global _global_client

    async with _global_client_lock:
        if _global_client is None:
            _global_client = await Client.connect(
                os.getenv("TEST_DEVICE_HOSTNAME"),
                int(os.getenv("TEST_DEVICE_PORT", 502)),
            )
        yield _global_client
