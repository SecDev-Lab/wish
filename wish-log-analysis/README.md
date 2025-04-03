# wish-log-analysis

Log analysis client package for wish.

## Overview

This package provides a client library that interfaces with the wish-log-analysis-api service to analyze command execution logs. It sends HTTP requests to the API server and processes the responses.

## Development

### Environment Variables

To use this package, you need to set up the following environment variables:

- `WISH_API_BASE_URL`: Base URL of the wish-log-analysis-api service (default: http://localhost:3000)

Example:

```bash
WISH_API_BASE_URL=http://localhost:3000
```

The client will automatically append the `/analyze` endpoint to the base URL.

## Integration with wish-log-analysis-api

This client library communicates with the wish-log-analysis-api service, which performs the actual log analysis using LangGraph. The client sends command execution results to the API and processes the responses.

For local development, you can run the API server locally using the instructions in the wish-log-analysis-api README.
