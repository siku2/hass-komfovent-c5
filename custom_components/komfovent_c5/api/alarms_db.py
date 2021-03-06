"""
CONFIRMED MAPPINGS:

001 = 0x0001 = 1B
127 = 0x007F = 127B
260 = 0x0104 = 4B   # from documentation

132 = 0x0084 = 5A
142 = 0x008E = 15A
211 = 0x00D3 = 84A
"""

_MESSAGES = {
    1: "LOW_SUPPLY_AIRFLOW",
    2: "LOW_EXTRACT_AIRFLOW",
    3: "VAV_CALIBRATION_FAIL",
    4: "CHANGE_OUTDOOR_AIR_FILTER",
    5: "CHANGE_EXTRACT_AIR_FILTER",
    12: "HIGH_PRESSURE_ON_COMPRESSOR",
    13: "LOW_PRESSURE_ON_COMPRESSOR",
    14: "SERVICE_TIME",
    15: "EVAPORATOR_ICING",
    16: "COMPRESSOR_FAILURE",
    19: "COMPRESSOR_OFF_AIRFLOW",
    20: "COMPRESSOR_OFF_TEMPERATURE",
    95: "LOW_HEAT_EXCHANGER_EFFICIENCY",
    112: "WATER_PUMP_OR_COIL_ALARM",
    127: "SERVICE_MODE",
}

ELECTRIC_HEATER_OFF_MSG = "ELECTRIC_HEATER_OFF"
ELECTRIC_HEATER_OFF_RANGE = range(6, 12)
COMPRESSOR_OFF_MALFUNCTION_MSG = "COMPRESSOR_OFF_MALFUNCTION"
COMPRESSOR_OFF_MALFUNCTION_RANGE = range(96, 112)


def code_str_from_code(code: int) -> str:
    code &= 0xFF
    if code > 0x7F:
        letter = "A"
        code -= 0x7F
    else:
        letter = "B"
    return f"{code}{letter}"


def message_for_code(code: int) -> str:
    code &= 0xFF
    try:
        return _MESSAGES[code]
    except KeyError:
        pass
    if code in ELECTRIC_HEATER_OFF_RANGE:
        return ELECTRIC_HEATER_OFF_MSG
    if code in COMPRESSOR_OFF_MALFUNCTION_RANGE:
        return COMPRESSOR_OFF_MALFUNCTION_MSG
    return "UNKNOWN"
