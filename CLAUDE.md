# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**wish** is an LLM-assisted shell for penetration testing that translates natural language "wishes" into executable shell commands. It provides a TUI (Text-based User Interface) for reviewing suggested commands, executing them, and monitoring their execution status. The system integrates with various security tools and supports both local execution and remote C2 operations.

## Key Development Commands

### Testing and Quality
```bash
# Root directory commands
make test             # Run unit tests across all projects
make integrated-test  # Run integration tests (requires API keys and .env)
make lint            # Run ruff linting
make format          # Auto-format with ruff

# Individual module testing
cd <module-name>
uv sync --dev        # Install dependencies
uv run pytest        # Run module tests
uv run pytest --ignore=tests/integrated/  # Run only unit tests
uv run pytest tests/integrated/  # Run only integration tests
```

### Running wish
```bash
# Install and run
pip install wish-sh
export OPENAI_API_KEY=your-api-key-here
wish  # or wish-sh on macOS

# Development mode
cd wish-sh
uv run wish
```

### API Services
```bash
# Start unified API Gateway
make run-api

# Run E2E tests
make e2e
```

## Architecture Overview

### Module Structure
- **wish-sh**: Main TUI application with WishManager orchestrator
- **wish-models**: Shared Pydantic models (CommandResult, Wish, etc.)
- **wish-command-generation**: LLM-based command generation with RAG capabilities
- **wish-command-generation-api**: Lambda-based API for command generation using LangGraph
- **wish-command-execution**: Command execution with multiple backends (Bash, Sliver C2)
- **wish-log-analysis**: Client library for command log analysis
- **wish-log-analysis-api**: Lambda-based API for LLM-powered log analysis
- **wish-knowledge-loader**: CLI tool for loading knowledge bases from GitHub repositories
- **wish-tools**: Framework for integrating security tools (msfconsole, etc.)
- **wish-api**: Unified API Gateway for all wish services

### Core Workflow
1. **User Input**: Natural language wishes in TUI
2. **Command Generation**: LLM converts wishes to executable commands using RAG
3. **Command Review**: User approves/modifies suggested commands
4. **Execution**: Commands run locally (Bash) or remotely (Sliver C2)
5. **Monitoring**: Real-time status tracking and log analysis
6. **Analysis**: LLM analyzes execution logs and determines success/failure

### Key Design Patterns
- **Modular Architecture**: Each component is independently packaged with uv
- **State Machine**: LangGraph manages command generation workflows
- **Factory Pattern**: Test factories in `test_factories/` for creating test data
- **Strategy Pattern**: Multiple execution backends (Bash, Sliver)
- **Client-Server**: API-based services for scalable command generation and analysis

## Development Environment

### Required Configuration
Create `.env` file in project root or set environment variables:
```
OPENAI_API_KEY=<your-key>
LANGCHAIN_API_KEY=<optional-for-langsmith>
LANGCHAIN_PROJECT=<optional-project-name>
```

### Testing Considerations
- Unit tests mock external dependencies (LLMs, APIs)
- Integration tests require real API connections and keys
- Use `@pytest.mark.parametrize` for testing multiple scenarios
- Test factories provide consistent test data across modules

## Common Patterns

### Adding New Features
1. Define models in `wish-models` if needed
2. Implement core logic in appropriate module
3. Add unit tests with mocked dependencies
4. Add integration tests for end-to-end validation
5. Update TUI flows in `wish-sh` if needed

### Adding New Tools
1. Extend `wish-tools` framework with new tool class
2. Follow the base tool interface pattern
3. Add comprehensive tests including integration tests
4. Document tool capabilities and usage

### Debugging Workflows
1. Use LangSmith tracing for detailed LLM interactions
2. Check logs in execution directories (timestamped)
3. Use individual module testing for isolated debugging
4. Review command generation API logs for generation issues

## Data Models

### Core Models (wish-models)
- **Wish**: Top-level user request with commands and execution state
- **CommandResult**: Execution results with logs, exit codes, and analysis
- **CommandInput**: Generated commands ready for execution
- **SystemInfo**: System context for command generation

### States and Lifecycle
- **Wish States**: PENDING → IN_PROGRESS → COMPLETED/FAILED
- **Command States**: TODO → RUNNING → SUCCESS/FAILED/TIMEOUT/CANCELLED
- **Execution Flow**: Generation → Review → Execution → Analysis → Completion

## Tool Integration

### Supported Tools
- **bash**: Local shell command execution
- **msfconsole**: Metasploit framework integration with automation support
- **sliver**: C2 framework for remote operations

### Tool Framework
Located in `wish-tools/`, provides:
- Base tool interface for consistent integration
- Tool registry for dynamic discovery
- Testing framework for tool validation
- Documentation generation for tool capabilities

## API Architecture

### Command Generation API
- **Endpoint**: Lambda-based API with LangGraph processing
- **Features**: RAG-enhanced generation, error handling, command optimization
- **Nodes**: feedback_analyzer, query_processor, command_generator, command_modifier

### Log Analysis API
- **Endpoint**: Lambda-based API for LLM-powered log analysis
- **Features**: Command state classification, log summarization
- **Processing**: Multi-stage analysis with result combination

## Common Development Tasks

### Running Tests
```bash
# All tests
make test

# Specific module
cd wish-sh && uv run pytest

# With coverage
cd wish-sh && uv run pytest --cov=wish_sh
```

### Code Quality
```bash
# Lint and format
make lint
make format

# Type checking (if configured)
cd <module> && uv run mypy src/
```

### Knowledge Base Management
```bash
# Load knowledge base
wish-knowledge-loader load --repo owner/repo --include "*.md"

# Search knowledge
wish-knowledge-loader search "nmap port scan"
```

## Security Considerations

- API keys should be set via environment variables, never committed
- Command execution is sandboxed where possible
- Remote execution through Sliver C2 requires proper authentication
- Log files may contain sensitive information and should be handled carefully
- Tool integrations follow security best practices for automated execution