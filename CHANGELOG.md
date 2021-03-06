# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.5] - 2022-08-01

### Fixed

- Debouncing for switches should actually work now.

## [0.2.4] - 2022-07-23

### Added

- Sensors for alarms.
- Service for resetting active alarms.

### Fixed

- No longer try to read 0 registers if no alarms are active.

## [0.2.3] - 2022-07-08

### Fixed

- Sensors based on the active mode now take into account that the active mode might be unavailable.
- Remove duplicate fields in services.yaml file.

## [0.2.2] - 2021-12-23

### Added

- "UNKNOWN" operation mode for mode 0, because the device reports it even though it's not documented to exist.

### Changed

- Hide "PROGRAM" and "UNKNOWN" operation mode from the mode select.

### Fixed

- AHU control switch wasn't working because it implemented the non-async family of functions.

## [0.2.1] - 2021-12-22

### Changed

- A few "level" sensors are undocumented deci percentages. Normalized to percentages with one decimal point.

## [0.2.0] - 2021-12-19

### Added

- Added installation instructions to the README
- Most registers from the "Monitoring" section are part of the API now
- Most sensors listed in the diagram of the reference manual are now available

## [0.1.0] - 2021-09-26

### Added

- Settings registers
- Modes registers
- Mode sensors and selects
- English and German translations

[Unreleased]: https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/compare/v0.2.5...main
[0.2.5]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.5
[0.2.4]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.4
[0.2.3]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.3
[0.2.2]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.2
[0.2.1]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.1
[0.2.0]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.0
[0.1.0]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.1.0
