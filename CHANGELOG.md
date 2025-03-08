# Changelog

All notable changes to the wish project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added system information collection capabilities for Sliver C2:
  - New model classes for system information (`SystemInfo`, `ExecutableInfo`, `ExecutableCollection`)
  - Factory classes for testing system information models
  - `SystemInfoCollector` for gathering OS information and executable files from remote systems
  - Integration with Sliver C2 backend to collect system information from compromised hosts

### Changed

### Fixed

### Removed


## [0.2.0] - 2025-03-08

### Added

- Added comprehensive documentation:
  - `docs/setup.md`: Installation and setup guide
  - `docs/usage-01-basic.md`: Basic usage guide
  - `docs/usage-02-knowledge-loader.md`: Knowledge loader usage guide
  - `docs/usage-03-C2.md`: Command and Control (C2) usage guide
- Added Sliver C2 integration:
  - New `SliverBackend` for executing commands on remote systems through Sliver C2
  - Command-line arguments `--sliver-config` and `--sliver-session` for connecting to Sliver C2
  - Automatic session detection when only one Sliver session is active

### Changed

### Fixed

### Removed


## [0.1.1] - 2025-03-08

### Added

- Added `wish-sh` command as an alternative to `wish` to avoid conflicts with macOS built-in Tcl/Tk `wish` command
- Added documentation for `wish-knowledge-loader` command in README

### Changed

### Fixed

### Removed


## [0.1.0] - 2025-03-08

### Added

- Initial release

### Changed

### Fixed

### Removed
