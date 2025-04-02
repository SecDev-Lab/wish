# wish-log-analysis-api

A serverless application that provides an API for analyzing command execution logs.

## Project Overview

This project receives command execution results (command, exit code, stdout, stderr), analyzes them using a LangGraph processing flow, and returns the results via an API.

### Main Features

- Command log summarization (using OpenAI language models)
- Command execution state classification
- Generation and return of analysis results

### Project Structure

- `src/wish_log_analysis_api` - Lambda function code for the application
  - `app.py` - Lambda handler
  - `graph.py` - LangGraph processing flow definition
  - `models.py` - Data models
  - `nodes/` - Processing nodes
- `tests` - Unit tests for the application code
- `template.yaml` - Template defining the application's AWS resources

## Development Process

### Environment Setup

To use this package, you need to set up the following environment variables:

1. Configure the required environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key (used by the API server)
   - `OPENAI_MODEL`: The OpenAI model to use (default: gpt-4o)
   - `WISH_LOG_ANALYSIS_API_URL`: URL of the wish-log-analysis-api service (default: http://localhost:3000/analyze)

Example:

```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
WISH_LOG_ANALYSIS_API_URL=http://localhost:3000/analyze
```

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

```bash
uv run pytest
```

### Graph Visualization

The log analysis graph can be visualized using the following command:

```bash
# Update graph visualization in docs/graph.svg and docs/design.md
uv sync --dev
uv run python scripts/update_graph_visualization.py
```

This will generate an SVG visualization of the graph and update the `docs/design.md` file.

## API Usage

The API provides an `/analyze` endpoint that receives command execution results via POST method and returns analysis results.

### Request Example

```json
{
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
}
```

### Response Example

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
