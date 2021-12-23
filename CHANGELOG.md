# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/compare/v0.2.1...main
[0.2.1]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.1
[0.2.0]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.2.0
[0.1.0]:      https://gitlab.bg12.ch/home-assistant/komfovent-c5/-/tags/v0.1.0
