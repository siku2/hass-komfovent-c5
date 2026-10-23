# Komfovent C5 Custom Animated Lovelace Dashboard Card for Home Assistant

This guide explains how to install and configure a native, responsive SVG-based custom Lovelace card (`komfovent-card`) to monitor and control a Komfovent C5 ventilation unit (AHU/VMC) integrated via Modbus TCP in Home Assistant.
<img width="3864" height="1848" alt="immagine" src="https://github.com/user-attachments/assets/8bda84c9-6ba8-4895-9a86-f62958b1908a" />

## Key Benefits Over `picture-elements`

* **100% Vector (SVG):** Eliminates alignment errors, clipping, and aspect-ratio distortion on smartphones and desktop browsers alike.
* **Theme-Aware:** Automatically adapts border, background, and text colors to light and dark themes using native Home Assistant CSS variables.
* **Hardware-Accelerated Animations:** Smooth CSS rotations for both fans and the heat recovery rotor, proportional to live operating speeds.
* **Fully Dynamic Configuration:** No hardcoded entities in the JavaScript source. All entity mappings and options are configured directly via Lovelace YAML.
* **Zero External Dependencies:** Does not require `card-mod` or external background raster images.

---

## 1. Installation

### Step 1: Create the Custom Card File

1. Access your Home Assistant configuration directory (using the Studio Code Server add-on, File Editor, SSH, or Samba share).
2. Inside the `/config/www/` folder, create (or replace) a file named `komfovent-card.js`.
3. Paste the komfovent-card.js JavaScript file code into `/config/www/komfovent-card.js`:



### Step 2: Register the Lovelace Resource

1. In Home Assistant, navigate to **Settings > Dashboards**.
2. Click the three dots (top right) and select **Resources**.
3. Click **Add Resource** (bottom right).
4. Enter:
   * **URL:** `/local/komfovent-card.js`
   * **Resource Type:** `JavaScript Module`
5. Click **Create**, then hard-refresh your browser (`Ctrl + F5` or `Cmd + Shift + R`).

---

## 2. Dashboard YAML Configuration

Add the card to any Lovelace view. You can customize the entity IDs to match your setup:

```yaml
type: vertical-stack
cards:
  - type: custom:komfovent-card
    title: Komfovent AHU
    # Temperatures
    t_outdoor: sensor.komfovent_outdoor_temperature
    t_supply: sensor.komfovent_supply_temperature
    t_extract: sensor.komfovent_extract_temperature
    t_exhaust: sensor.komfovent_exhaust_temperature
    # Setpoints
    set_supply: sensor.komfovent_supply_temperature_setpoint
    set_extract: sensor.komfovent_extract_temperature_setpoint
    # Airflow
    flow_supply: sensor.komfovent_supply_airflow
    flow_extract: sensor.komfovent_extract_airflow
    # Fans
    fan_supply: sensor.komfovent_supply_fan_level
    fan_extract: sensor.komfovent_extract_fan_level
    # Heat Exchanger
    rotor: sensor.komfovent_heat_exchanger_level
    efficiency: sensor.komfovent_heat_exchanger_efficiency
    # Auxiliaries
    heater: sensor.komfovent_electric_heater_level
    aqi: sensor.komfovent_air_quality_level

  - type: entities
    title: AHU Operations & Controls
    show_header_toggle: false
    entities:
      - entity: switch.komfovent_ahu_power
        name: Unit Power
        icon: mdi:power
      - entity: select.komfovent_operation_mode
        name: Operating Mode
        icon: mdi:tune-vertical
      - entity: select.komfovent_temperature_control_mode
        name: Temperature Control
        icon: mdi:thermometer-auto
      - type: divider
      - entity: sensor.komfovent_active_alarms
        name: Active Alarms
        icon: mdi:alert-circle-outline
```

---

## 3. Configuration Reference

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `title` | string | Optional | Header title shown at top of the card |
| `t_outdoor` | entity_id | Optional | Outdoor air temperature intake (°C) |
| `t_supply` | entity_id | Optional | Supply air temperature into rooms (°C) |
| `t_extract` | entity_id | Optional | Extract air temperature from rooms (°C) |
| `t_exhaust` | entity_id | Optional | Exhaust air temperature blown outside (°C) |
| `set_supply` | entity_id | Optional | Supply temperature setpoint (°C) |
| `set_extract` | entity_id | Optional | Extract temperature setpoint (°C) |
| `flow_supply`| entity_id | Optional | Supply airflow rate (m³/h) |
| `flow_extract`| entity_id | Optional | Extract airflow rate (m³/h) |
| `fan_supply` | entity_id | Optional | Supply fan speed percentage (0–100%) |
| `fan_extract`| entity_id | Optional | Extract fan speed percentage (0–100%) |
| `rotor` | entity_id | Optional | Rotary exchanger speed percentage (0–100%) |
| `efficiency` | entity_id | Optional | Heat recovery efficiency percentage (%) |
| `heater` | entity_id | Optional | Electric/water heater level percentage (%) |
| `aqi` | entity_id | Optional | Air Quality Index / VOC sensor reading |
