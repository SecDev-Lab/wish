# wish-command-generation

Command generation client package for wish.

## Overview

This package provides a client library that interfaces with the wish-command-generation-api service to generate shell commands based on natural language queries. It sends HTTP requests to the API server and processes the responses.

## Development

### Environment Variables

To use this package, you need to set up the following environment variables:

- `WISH_API_BASE_URL`: Base URL of the wish-command-generation-api service (default: http://localhost:3000)

Example:

```bash
WISH_API_BASE_URL=http://localhost:3000
```

The client will automatically append the `/generate` endpoint to the base URL.

## Integration with wish-command-generation-api

This client library communicates with the wish-command-generation-api service, which performs the actual command generation using LangGraph. The client sends natural language queries to the API and processes the responses.

For local development, you can run the API server locally using the instructions in the wish-command-generation-api README.
