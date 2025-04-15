# wish-api

RapidPen Cloud - Unified API Gateway for wish services

## Overview

This project integrates `wish-command-generation-api` and `wish-log-analysis-api`, providing them through a single API Gateway. Both APIs share the same API Gateway while maintaining their own endpoints:

- `/generate` - Command Generation API (wish-command-generation-api)
- `/analyze` - Log Analysis API (wish-log-analysis-api)

## Architecture

The architecture of the unified API is as follows:

```
wish-api/
  |
  ├── Shared API Gateway
  |     |
  |     ├── /generate endpoint ──→ GenerateFunction (wish-command-generation-api)
  |     |
  |     └── /analyze endpoint ──→ AnalyzeFunction (wish-log-analysis-api)
  |
  └── Common settings and parameters
```

This structure allows each API to be developed and maintained independently, while deployment and operations are integrated.

## Dependencies

This project depends on the following packages:

- wish-command-generation-api
- wish-log-analysis-api
- aws-sam-cli

## Setup and Execution

### Prerequisites

- Python 3.13 or higher
- uv (Python dependency management tool)
- AWS SAM CLI

### Setting up the Local Development Environment

1. Install dependencies:

```bash
cd wish-api
uv sync --dev
```

2. Set environment variables:

Environment variables are set in the `~/.wish/env` file. The required environment variables are:

```
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
WISH_API_BASE_URL=http://localhost:3000
LANGCHAIN_API_KEY=your-langchain-api-key-here
```

### Starting the API

From the top-level directory:

```bash
make run-api
```

Or directly from the wish-api directory:

```bash
cd wish-api
make run-api
```

This will start the API Gateway locally, making the following endpoints available:

- `http://localhost:3000/generate` - Command Generation API
- `http://localhost:3000/analyze` - Log Analysis API

## API Usage

### Command Generation API

**Endpoint**: `/generate`

**Method**: POST

**Request Body**:

```json
{
  "query": "Show information about network interfaces",
  "context": {
    "os": "linux",
    "shell": "bash"
  }
}
```

**Response**:

```json
{
  "command": "ip addr show",
  "explanation": "This command displays all network interfaces and their IP address information on the system."
}
```

### Log Analysis API

**Endpoint**: `/analyze`

**Method**: POST

**Request Body**:

```json
{
  "command": "ls -la",
  "output": "total 32\ndrwxr-xr-x  5 user  staff   160 Apr 15 10:00 .\ndrwxr-xr-x  3 user  staff    96 Apr 15 09:50 ..\n-rw-r--r--  1 user  staff  1024 Apr 15 10:00 file1.txt\n-rw-r--r--  1 user  staff  2048 Apr 15 10:00 file2.txt"
}
```

**Response**:

```json
{
  "analysis": "This directory contains two files (file1.txt and file2.txt). The size of file1.txt is 1024 bytes, and the size of file2.txt is 2048 bytes. Both files were created or modified today (April 15)."
}
```

## Development Guidelines

### Project Structure

```
wish-api/
├── Makefile           # Build and run commands
├── README.md          # This file
├── pyproject.toml     # Project settings and dependencies
├── scripts/           # Utility scripts
│   ├── env_to_json.py        # Convert environment variables to JSON for SAM
│   └── generate_requirements.py  # Generate requirements.txt
└── template.yaml      # SAM template (API definition)
```

### Development Workflow

1. Install dependencies: `uv sync --dev`
2. Test locally: `make run-api`
3. Deploy: `sam deploy --guided`

### Adding New Endpoints

To add a new endpoint, follow these steps:

1. Create or update the corresponding API project
2. Add a new Lambda function and endpoint to `wish-api/template.yaml`
3. Update `wish-api/scripts/env_to_json.py` as needed to set environment variables for the new function

### Testing

Each API project has its own tests, but integration testing is also important. To run integration tests:

```bash
cd wish-api
uv run pytest tests/
```

## Deployment

Deploy using AWS SAM:

```bash
cd wish-api
sam deploy --guided
```

During the first deployment, you'll set the required parameters interactively. For subsequent deployments, you can use the saved settings:

```bash
sam deploy
```

## Troubleshooting

### Common Issues

1. **API Gateway doesn't start**
   - Check that dependencies are correctly installed
   - Ensure SAM CLI is the latest version
   - Check if port 3000 is being used by another process

2. **Lambda function returns an error**
   - Check that environment variables are correctly set
   - Ensure dependencies are correctly installed
   - Check logs (using the `sam logs` command)

### Checking Logs

To check logs during local development, look at the terminal window where you started the API Gateway.

To check logs in a deployed environment:

```bash
sam logs -n FunctionName --stack-name wish-api-stack
```

## Notes

- This project reuses the code from existing `wish-command-generation-api` and `wish-log-analysis-api` packages, directly referencing their handlers.
- Be careful to avoid dependency conflicts between the two API packages.

## References

- [AWS SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
- [Lambda Documentation](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
