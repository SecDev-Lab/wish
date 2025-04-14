# wish-log-analysis-api

A serverless application that provides both an API and a library for analyzing command execution logs.

## Project Overview

This project receives command execution results (command, exit code, stdout, stderr), analyzes them using a LangGraph processing flow, and returns the results via an API or library interface.

### Main Features

- Command log summarization (using OpenAI language models)
- Command execution state classification
- Generation and return of analysis results

### Project Structure

- `src/wish_log_analysis_api` - Lambda function code for the application
  - `app.py` - Lambda handler
  - `config.py` - Configuration class
  - `core/` - Core functionality
    - `analyzer.py` - Command result analysis function
  - `graph.py` - LangGraph processing flow definition
  - `models.py` - Data models
  - `nodes/` - Processing nodes
- `tests` - Tests for the application code
  - `unit/` - Unit tests
  - `integration/` - Integration tests
- `scripts` - Utility scripts
- `template.yaml` - Template defining the application's AWS resources

## Development Process

### Environment Setup

To use this package, you need to set up the following environment variables in your `~/.wish/env` file:

1. Configure the required environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key (used by the API server)
   - `OPENAI_MODEL`: The OpenAI model to use (default: gpt-4o)
   - `WISH_API_BASE_URL`: Base URL of the wish-log-analysis-api service (default: http://localhost:3000)

Example:

```
# OpenAI API settings
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o

# API settings
WISH_API_BASE_URL=http://localhost:3000
```

Environment variables are automatically loaded from the `~/.wish/env` file and passed to the SAM local container.

The client will automatically append the `/analyze` endpoint to the base URL.

### Build

```bash
make build
```

Builds the application using SAM (with container).

### Start Local Development Server

```bash
make run-api
```

Starts a local development server to test the API.

### Clean Up

```bash
make clean
```

Cleans up generated files.

### Testing

#### Unit Tests

```bash
uv run pytest tests/unit
```

Unit tests verify the functionality of individual components without external dependencies.

#### Integration Tests

```bash
uv run pytest tests/integration -m integration
```

Integration tests verify the functionality of the library as a whole, including interactions with external services.

#### All Tests

```bash
uv run pytest
```

This command runs all tests in the project.

#### E2E Tests

```bash
make e2e
```

E2E tests are executed against a deployed API endpoint. These tests are designed to be run from another repository or deployment environment that references this repository.

To run E2E tests, you need to set the following environment variables in the `.env.test` file:

- `API_ENDPOINT`: URL of the deployed API endpoint (e.g., `https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/stg`)
- `API_KEY`: Key for API access

When the `make e2e` command is executed from a parent repository, the tests will run against the remote API endpoint specified in these environment variables.

### Graph Visualization

The log analysis graph can be visualized using the following command:

```bash
# Update graph visualization in docs/graph.svg and docs/design.md
uv sync --dev
uv run python scripts/update_graph_visualization.py
```

This will generate an SVG visualization of the graph and update the `docs/design.md` file.

## Usage

### Using as an API

#### API Request Example

```bash
curl -X POST http://localhost:3000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "command_result": {
      "num": 1,
      "command": "ls -la",
      "exit_code": 0,
      "log_files": {
        "stdout": "/path/to/stdout.log",
        "stderr": "/path/to/stderr.log"
      },
      "created_at": "2025-04-02T12:00:00Z",
      "finished_at": "2025-04-02T12:00:01Z"
    }
  }'
```

#### API Response Example

```json
{
  "analyzed_command_result": {
    "num": 1,
    "command": "ls -la",
    "state": "SUCCESS",
    "exit_code": 0,
    "log_summary": "Displayed directory file listing. Total of 10 files exist and all were displayed successfully.",
    "log_files": {
      "stdout": "/path/to/stdout.log",
      "stderr": "/path/to/stderr.log"
    },
    "created_at": "2025-04-02T12:00:00Z",
    "finished_at": "2025-04-02T12:00:01Z"
  }
}
```

### Using as a Library

#### Installation

```bash
pip install git+https://github.com/SecDev-Lab/wish-log-analysis-api.git
```

#### Basic Usage

```python
from wish_log_analysis_api.core.analyzer import analyze_command_result
from wish_log_analysis_api.models import AnalyzeRequest
from wish_log_analysis_api.config import AnalyzerConfig
from wish_models.command_result import CommandResult
from wish_models.command_result.log_files import LogFiles
from pathlib import Path

# Create command result
command_result = CommandResult(
    num=1,
    command="ls -la",
    exit_code=0,
    log_files=LogFiles(
        stdout=Path("/path/to/stdout.log"),
        stderr=Path("/path/to/stderr.log")
    ),
    created_at="2025-04-02T12:00:00Z",
    finished_at="2025-04-02T12:00:01Z"
)

# Create request
request = AnalyzeRequest(command_result=command_result)

# Run analysis with default configuration (loads from environment variables)
response = analyze_command_result(request)

# Or run analysis with custom configuration
config = AnalyzerConfig(
    openai_api_key="your-api-key-here",
    openai_model="gpt-4o"
)
response = analyze_command_result(request, config=config)

# Get results
analyzed_result = response.analyzed_command_result
print(f"State: {analyzed_result.state}")
print(f"Summary: {analyzed_result.log_summary}")
```

#### Advanced Usage

```python
from wish_log_analysis_api.graph import create_log_analysis_graph
from wish_log_analysis_api.models import GraphState
from wish_log_analysis_api.config import AnalyzerConfig

# Create custom configuration
config = AnalyzerConfig(
    openai_model="gpt-4o",
    langchain_tracing_v2=True
)

# Create graph directly
graph = create_log_analysis_graph(config=config)

# Create initial state
initial_state = GraphState(command_result=command_result)

# Run graph
result = graph.invoke(initial_state)

# Get results
analyzed_result = result.analyzed_command_result
```
