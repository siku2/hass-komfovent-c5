import os

import pytest
from komfovent_c5.api import (
    Client,
    FlowControlMode,
    Mode,
    Modes,
    OperationMode,
    SpecialMode,
    TemperatureControlMode,
    VavStatus,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client() -> Client:
    client = await Client.connect(
        os.getenv("TEST_DEVICE_HOSTNAME"), int(os.getenv("TEST_DEVICE_PORT", 502))
    )
    yield client


async def test_modes(client: Client):
    modes = Modes(client)

    assert await modes.ahu_on() in (True, False)
    assert await modes.operation_mode() in OperationMode.__members__.values()
    assert await modes.flow_control_mode() in FlowControlMode.__members__.values()
    assert (
        await modes.temperature_control_mode()
        in TemperatureControlMode.__members__.values()
    )
    assert await modes.vav_status() in VavStatus.__members__.values()
    assert 100 <= await modes.vav_sensors_range() <= 5000
    assert 0 <= await modes.nominal_supply_pressure() <= 4500
    assert 0 <= await modes.nominal_exhaust_pressure() <= 4500


async def test_mode_registers(client: Client):
    modes = Modes(client)

    async def check_mode_registers(mode: Mode):
        assert await mode.supply_flow() >= 0
        assert await mode.extract_flow() >= 0
        assert 5.0 <= await mode.setpoint_temperature() <= 40.0

        if isinstance(mode, SpecialMode):
            assert await mode.configuration() is not None

    await check_mode_registers(modes.mode_registers(OperationMode.COMFORT1))
    await check_mode_registers(modes.mode_registers(OperationMode.COMFORT2))
    await check_mode_registers(modes.mode_registers(OperationMode.ECONOMY1))
    await check_mode_registers(modes.mode_registers(OperationMode.ECONOMY2))
    await check_mode_registers(modes.mode_registers(OperationMode.SPECIAL))


async def test_read_all(client: Client):
    modes = Modes(client)

    state = await modes.read_all()
    assert state.modes[OperationMode.SPECIAL].configuration is not None
