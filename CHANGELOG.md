# Changelog

All notable changes to the wish project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed


## [0.6.7] - 2025-04-18

### Added

- Added Qdrant vector store support to wish-command-generation-api:
  - Added optional Qdrant integration as an alternative to ChromaDB
  - Added feature-based dependencies with `[qdrant]` extra in pyproject.toml
  - Added configuration options for Qdrant in settings.py
  - Updated documentation with Qdrant setup and usage instructions

### Changed

- Refactored RAG implementation in wish-command-generation-api:
  - Improved code organization with separate functions for different vector stores
- Restructured dependencies to make vector store backends truly optional:
  - Moved ChromaDB from base dependencies to optional `[chroma]` extra
  - Updated code to handle missing dependencies gracefully with clear error messages

### Fixed

### Removed


## [0.6.6] - 2025-04-18

### Added

- Added CommandInputFactory for generating CommandInput instances

### Changed

### Fixed

### Removed


## [0.6.5] - 2025-04-15

### Added

### Changed

- Changed Python version requirement from >=3.13 to >=3.10:
  - Updated `requires-python` in all packages' pyproject.toml files
  - Added Python 3.10, 3.11, and 3.12 to classifiers in all packages
  - Updated documentation to reflect new minimum Python version requirement

### Fixed

### Removed


## [0.6.4] - 2025-04-15

### Added

### Changed

### Fixed

### Removed


## [0.6.4-a1] - 2025-04-15

### Added

### Changed

### Fixed

### Removed


## [0.6.1] - 2025-04-15

### Added

- Added unified API Gateway for wish services:
  - Created new `wish-api` package that integrates multiple API services
  - Combined `wish-command-generation-api` and `wish-log-analysis-api` under a single API Gateway
  - Added top-level `make run-api` command to start the unified API
  - Added API development documentation in `docs/api-development.md`

### Changed

### Fixed

### Removed


## [0.6.0] - 2025-04-14

### Added

- Added library interface to wish-log-analysis-api:
  - Refactored code structure to support both API and library usage
  - Added core/analyzer.py with analyze_command_result function that accepts custom configuration
  - Added config.py with AnalyzerConfig class for flexible configuration
  - Added comprehensive documentation for library usage in README.md
  - Added unit and integration tests for library functionality

### Changed

- Improved project organization in wish-log-analysis-api:
  - Restructured test directory with separate unit/ and integration/ folders
  - Updated project description to reflect dual API/library nature
  - Made test assertions more flexible to accommodate different response formats

### Fixed

- Fixed error handling in wish-log-analysis-api:
  - Fixed Lambda handler to properly return error responses when analyze_command_result returns an error
  - Ensured error messages are correctly included in API responses for invalid requests
  - Fixed failing test case in test_handler_invalid_request

### Removed


## [0.5.1] - 2025-04-11

### Added

### Changed

### Fixed

- Improved API key settings
  - Changed OPENAI_API_KEY from required field to default value with warning message
    - Before: `Field(...)` (required parameter)
    - After: `Field(default="WARNING: Set OPENAI_API_KEY env var or in .env file to use OpenAI features")`
  - Changed LANGCHAIN_API_KEY from required field to default value with warning message
    - Before: `Field(...)` (required parameter)
    - After: `Field(default="WARNING: Set LANGCHAIN_API_KEY env var or in .env file to use LangChain features")`

### Removed


## [0.5.0] - 2025-04-03

### Added
- Added new `wish-log-analysis-api` package:
  - Implemented serverless API using AWS Lambda and API Gateway
  - Created LangGraph-based analysis pipeline for command logs
  - Added SAM template for AWS deployment
  - Added GitHub Actions workflow for automated deployment

### Changed
- Refactored `wish-log-analysis` to client-server architecture:
  - Converted `wish-log-analysis` to API client
  - Moved analysis logic to `wish-log-analysis-api` service
  - Updated documentation to reflect new architecture
- Updated environment configuration and dependencies

### Fixed

### Removed


## [0.4.5] - 2025-03-17

### Added

- YouTube movies in documents

### Changed

- Use OpenAI Response API.

### Fixed

### Removed


## [0.4.4] - 2025-03-10

### Added

### Changed

- Prefer parallel commands

### Fixed

### Removed


## [0.4.3] - 2025-03-10

### Added

### Changed

### Fixed
- Improved command execution in Windows environments:
  - Updated to execute commands through cmd.exe on Windows systems
  - Added proper command argument splitting for Windows

### Removed


## [0.4.2] - 2025-03-10

### Added

- Added error modal for command generation failures:
  - Improved error handling to display errors in a modal dialog instead of command suggestion screen
  - Enhanced user experience by keeping users in the wish input screen when errors occur
  - Added detailed error information display including the command generation response

### Changed

### Fixed

### Removed


## [0.4.1] - 2025-03-09

### Added

### Changed

### Fixed

- Fixed embedding model configuration in wish-knowledge-loader:
  - Updated vector_store.py to use OPENAI_EMBEDDING_MODEL instead of OPENAI_MODEL for embeddings
  - Added OPENAI_EMBEDDING_MODEL configuration to .env.example
  - Updated docs/setup.md with instructions for setting up OPENAI_EMBEDDING_MODEL
  - Fixed "You are not allowed to generate embeddings from this model" error
- Fixed JSON parsing in command generation:
  - Added explicit instruction to avoid code block markers like ```json in the prompt
  - Improved prompt to clarify that output is parsed directly as JSON
  - Enhanced error handling for invalid JSON responses

### Removed


## [0.4.0] - 2025-03-09

### Added

- Added comprehensive whitepaper:
  - `docs/whitepaper.md`: Technical whitepaper describing wish architecture, features, and development roadmap
  - Detailed comparison with similar tools in the penetration testing space
  - Explanation of wish's role in the RapidPen ecosystem
- Added knowledge management features to wish-knowledge-loader:
  - New `list` command to display all loaded knowledge bases
  - New `delete` command to remove knowledge bases when no longer needed
  - Smart repository management that preserves shared repositories
  - Improved CLI with subcommands for better organization

### Changed

### Fixed

### Removed


## [0.3.2] - 2025-03-09

### Added

### Changed

### Fixed

- Fixed handling of dead Sliver sessions:
  - Added validation to check if a Sliver session is in an invalid state
  - Improved error reporting for dead sessions with clear error messages
  - Prevented command execution on invalid sessions to avoid unexpected behavior

### Removed


## [0.3.1] - 2025-03-09

### Added

- Added support for custom .env file path:
  - Added `--env-file` command-line option to specify a custom .env file path
  - Default path is `$WISH_HOME/env`
  - Centralized settings management in `wish-models` package

### Changed

- Refactored settings management:
  - Moved settings from individual packages to `wish-models` package
  - All packages now use the same settings instance

### Fixed

- Fixed LangSmith integration:
  - Added automatic environment variable setup for LangChain/LangGraph tracing
  - Settings values are now properly passed to LangSmith via environment variables
- [wish-command-generation] Fixed a bug where the target machine environment from Sliver was not properly reflected in command generation

### Removed


## [0.3.0] - 2025-03-08

### Added

- Added system information collection capabilities for Sliver C2:
  - New model classes for system information (`SystemInfo`, `ExecutableInfo`, `ExecutableCollection`)
  - Factory classes for testing system information models
  - `SystemInfoCollector` for gathering OS information and executable files from remote systems
  - Integration with Sliver C2 backend to collect system information from compromised hosts
- Added OS-aware command generation:
  - Enhanced command generation to use system information for creating OS-specific commands
  - Updated prompts to include examples for different operating systems (Linux, Windows, macOS)
  - Improved user experience by generating commands that are compatible with the user's system

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
