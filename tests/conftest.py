import os
import sys
from pathlib import Path

import pytest

CUSTOM_COMPONENTS_PATH = (Path(__file__) / "../../custom_components").resolve()
sys.path.append(str(CUSTOM_COMPONENTS_PATH))


from komfovent_c5.api import Client


@pytest.fixture
async def client() -> Client:
    client = await Client.connect(
        os.getenv("TEST_DEVICE_HOSTNAME"), int(os.getenv("TEST_DEVICE_PORT", 502))
    )
    yield client
