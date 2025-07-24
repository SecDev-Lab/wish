# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### Environment Characteristics

- **The repo root is the pwd where Claude Code is opened. While ../../ is also the repo root due to using sprout, treat the pwd (worktree) as the repo root**

## Work Attitude and Quality Management

**Important**: Claude Code should act as a careful veteran engineer. Prioritize quality and reliability over implementation speed.

### Basic Principles
- Critically verify when you think implementation is complete
- Don't just think "it works", ask "does it really work correctly?"
- Actively consider potential problems and edge cases
- Don't skimp on testing and validation, be more thorough than necessary. Validation policy:
  - Actively use headless mode (calling the `HeadlessWish` class) for integrated verification except UI
  - Make actual communications to target machines and OpenAI API
  - Verify UI-related parts as much as possible yourself, but ask humans for difficult parts
- Always be skeptical of your own implementation and verify from multiple perspectives

### Pre-Implementation Checklist
- Detailed investigation of existing code (related files, dependencies, impact scope)
- Understanding of design patterns and coding conventions
- Consideration of test case coverage
- Verification of error handling appropriateness

### Post-Implementation Required Verification
1. **Code Quality**: Static analysis with `make lint`, `make format`
2. **Unit Tests**: Run all package tests with `make test`
3. **Integration Tests**: Comprehensive validation with `+uat`
4. **Manual Verification**: Confirm actual use case operation
5. **Error Cases**: Verify abnormal behavior
6. **Performance**: Test under unexpected load
7. **Compatibility**: Check impact on existing features

### Quality Standards
- All tests passing is the minimum requirement
- Zero static analysis errors is a prerequisite
- Confirmed to work in actual usage scenarios
- Appropriate behavior for edge cases and abnormal conditions
- Documentation updated (as needed)

### Error Handling and Fail-Fast Policy

**Important**: This repository adopts the fail-fast principle, prioritizing early error detection over recovery.

#### Basic Policy
- Immediately fail with exceptions for programming errors like type errors instead of handling with conditional branches
- Avoid continuing operation in uncertain states
- Emphasize early error detection and clear failures

#### Implementation Guidelines
- Immediately fail with exceptions for programming errors
- Only use WARN/ERROR logs for unexpected situations due to user environment factors
- Allow exceptional handling only for special reasons with explicit documentation

## Language Settings

Responses and document file generation should primarily be in English. Use English in the following cases:
- Comments, variable names, and function names in code
- Additions or modifications to existing English documentation
- When the user asks questions in English

## Specification Management

When developing new features, place specifications under `docs/(short-english-phrase-describing-feature)/*.md` in English.
These specifications serve as references during implementation, but more importantly, they help review "what was the purpose, how, and what was implemented" after implementation.

## Intermediate File Management

### Using the tmp/ Directory
All intermediate files created by Claude Code (test files, planning documents, temporary work files, etc.) must be created under the `tmp/` directory.

**Target Files**:
- Test sample files
- Implementation planning documents
- Debug temporary files
- Verification scripts
- Other temporary work files

**Exceptions**:
- Official project files (source code, configuration files, official documentation, etc.)
- When the user explicitly specifies another location

### Cleanup
The `tmp/` directory is regularly cleaned up:
- When executing the `+brc` command
- When executing the `+review` command
- During other quality management tasks

## Project Overview

wish is a Workflow-Aware AI Command Center that recognizes penetration testers' workflows and accelerates their thinking. By remembering and interpreting the results of commands executed by testers and suggesting the next logical move based on the situation, it dramatically reduces the cost of context switching.

## Key Development Commands

### Testing and Quality

```bash
# Basic commands (to be adjusted according to project structure)
make test             # Run unit tests
make lint            # Run ruff linting
make format          # Auto-format with ruff

# Python environment management
uv sync              # Install dependencies
uv sync --dev        # Install with dev dependencies
uv run pytest        # Run tests
```

### User Acceptance Testing (UAT)
```bash
# Complete system validation (shortcut command)
+uat                  # Run comprehensive UAT including code quality, tests, and functionality checks
```

### Running wish
```bash
# Installation
pip install wish-sh

# Basic usage
wish                  # Start the interactive CLI
```

## Architecture Overview

### Key Features
- **Hybrid CLI**: Supports both AI dialogue and direct command execution
- **State Management**: Internally maintains target information and discovered host/port information
- **AI Suggestions**: LLM suggests the next command to execute based on current state and context
- **Asynchronous Job Management**: Asynchronous execution of time-consuming commands and non-freezing UI
- **Knowledge Base**: RAG (Retrieval-Augmented Generation) utilizing HackTricks
- **C2 Integration**: Basic integration features with Sliver C2

## Development Environment

### Required Configuration

#### OpenAI API Key Setup

The AI functionality requires an OpenAI API key. Configure it using one of these methods:

**Method 1: Environment Variable (Highest Priority)**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Method 2: Configuration File (Fallback)**
```bash
# Initialize configuration file
wish-ai-validate --init-config

# Set your API key
wish-ai-validate --set-api-key "your-openai-api-key-here"
```

Or manually edit `~/.wish/config.toml`:
```toml
[llm]
api_key = "your-openai-api-key-here"
model = "gpt-4o"
max_tokens = 8000
temperature = 0.1
```

**Configuration Priority:**
1. **OPENAI_API_KEY environment variable** (Highest priority)
2. **~/.wish/config.toml [llm.api_key]** (Fallback)
3. **None** (fail-fast - immediate error)

**Environment Variable Advantages:**
- **Development/CI environments**: Reliable configuration in development environments and CI/CD pipelines
- **Highest priority**: Reliably overrides other settings
- **Security**: Temporary setting that is not persisted

**Configuration File Advantages:**
- **Usability**: Intuitive and easy to understand for general users
- **Persistence**: Settings are retained after restart
- **Security**: Automatic protection with appropriate file permissions (600)
- **CLI support**: Easy configuration management with `wish-ai-validate` command

**Security Considerations:**
- ⚠️ **Never commit API keys to version control**
- Configuration files are automatically protected with 600 permissions
- Use different keys for development and production
- Regularly rotate API keys for security

#### Configuration Management Best Practices

**Configuration File Management:**
```bash
# Initialize configuration file
wish-ai-validate --init-config

# Set API key
wish-ai-validate --set-api-key "your-api-key-here"

# Check and validate configuration
wish-ai-validate

# Environment check only
wish-ai-validate --check-env
```

**Troubleshooting:**
- Configuration file not found: `wish-ai-validate --init-config`
- Invalid API key: `wish-ai-validate --set-api-key "new-key"`
- Permission errors: `chmod 600 ~/.wish/config.toml`

#### Additional Configuration

Place VPN config at `HTB.ovpn` for HackTheBox connectivity.

### Docker Environment
- Base image: Kali Linux with security tools pre-installed
- VPN support for isolated testing environments
- Mounted volumes for logs and results

### Testing Considerations
- Unit tests mock external dependencies (LLMs, APIs)
- Tests use the configuration hierarchy (environment → config file → defaults)
- Use `@pytest.mark.parametrize` for testing multiple scenarios

## Session Management

wish uses lightweight SessionMetadata for state management:
- Simple session tracking with basic metadata
- Command history (latest 100 commands)
- Mode tracking (recon, enum, exploit, etc.)
- Engagement state with targets, hosts, findings, and collected data
- In-memory only - no complex persistence or task trees

## Development Workflows

### Monorepo Development
1. **Setup**: `uv sync --all-packages --dev` to install all dependencies
2. **Testing**: `make test` for all packages, or `cd <package> && uv run pytest` for individual
3. **Quality**: `make lint` and `make format` for code quality
4. **Building**: `docker compose build` for containerized testing

### Adding New Features
1. Define models in `wish-models`
2. Implement logic in appropriate module
3. Add unit tests with mocked dependencies
4. Add unit tests for validation
5. Update workflow in main package if needed

### Logging Guidelines
When implementing logging in any module:
1. **Import**: Use Python standard logging
2. **Initialize**: Create logger with `logger = logging.getLogger(__name__)`
3. **Configuration**: Use centralized logging configuration
4. **Log Levels**: Use standard levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) as appropriate

Example:
```python
import logging

logger = logging.getLogger(__name__)

# Use logger normally
logger.info("Processing task")
logger.error(f"Failed to process: {error}")
```

### Debugging Workflows
1. Check logs for error messages
2. Use appropriate debugging tools
3. Enable verbose logging when needed

### Before Completing Your Task

Always validate your implementation by running:
1. `make test` (run all tests)
2. `make lint` (check code quality)
3. `make format` (format code)
4. Any specific tests affected by your changes



## Slash Commands

This project defines slash commands to streamline repetitive workflows.
Markdown files defined in the `.claude/commands/` directory are available as slash commands.
Typing `/` when inputting will display a list of available commands.

- `/brc`: Branch review & cleanup
- `/e2e`: Run end-to-end tests
- `/fixci`: Fix CI
- `/fixlint`: Fix linting
- `/fixtest`: Fix tests
- `/pr`: Create pull request

## Task Completion Notification

When Claude Code completes any task in this repository, provide a clear summary of the work completed.

This should be done after:
- Completing code modifications
- Finishing test runs
- Completing refactoring tasks
- Finishing any requested operation
- Any other task completion


## Sliver C2 Integration

### Development Configuration Files
Use the following configuration files for development and testing:
- For testing: `~/.sliver-client/configs/wish-test.cfg`
- This is the standard name used in CI and automated tests

### End-User Configuration
Recommended for end users:
1. Standard configuration file: `~/.sliver-client/configs/wish.cfg`
2. Specify via environment variable: `export WISH_C2_SLIVER_CONFIG=/path/to/config.cfg`
3. Configuration in config.toml

### Generating Configuration Files
```bash
# For development environment (when running Claude Code)
sliver-server operator --name wish-test --lhost localhost --save ~/.sliver-client/configs/wish-test.cfg

# For end users
sliver-server operator --name $USER --lhost localhost --save ~/.sliver-client/configs/wish.cfg
```

### Test Execution Notes
- `wish-test.cfg` is required when running `pytest`
- If the file doesn't exist, Sliver integration tests will be skipped

## Python Environment and Command Execution Notes

### Notes for Python-Related Command Execution
- Always prefix Python-related commands with `uv run`
- **Claude hooks**: Direct python/pip execution is automatically blocked by `.claude/hooks/enforce-uv.sh`, and appropriate `uv run` commands are suggested
- Examples:
  - ❌ `python script.py` → ✅ `uv run python script.py`
  - ❌ `pytest` → ✅ `uv run pytest`
  - ❌ `pip install package` → ✅ `uv add package`

