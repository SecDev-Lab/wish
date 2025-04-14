# Command Generation Client Design

This document describes the design of the command generation client.

## Overview

The command generation client is a Python library that interfaces with the wish-command-generation-api service to generate shell commands based on natural language queries. It provides a simple API for sending queries to the service and processing the responses.

## Architecture

The client is designed as a lightweight HTTP client that communicates with the wish-command-generation-api service. It handles request formatting, error handling, and response parsing.

## Components

### Configuration

The `ClientConfig` class manages configuration settings for the client, including:

- API base URL
- Generate endpoint URL

Configuration can be loaded from environment variables or provided directly.

### Models

The client uses the following data models:

- `GeneratedCommand`: Represents a generated shell command with explanation
- `GenerateRequest`: Request model for the generate endpoint
- `GenerateResponse`: Response model from the generate endpoint

### Client

The `CommandGenerationClient` class provides the main functionality:

- Initializing with configuration
- Sending requests to the API
- Handling responses and errors

A convenience function `generate_command()` is also provided for simple usage.

## Usage

### Basic Usage

```python
from wish_command_generation import generate_command

# Generate a command
response = generate_command(
    query="list all files in the current directory",
    context={
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }
)

# Use the generated command
print(f"Command: {response.generated_command.command}")
print(f"Explanation: {response.generated_command.explanation}")
```

### Advanced Usage

```python
from wish_command_generation.client import CommandGenerationClient
from wish_command_generation.config import ClientConfig

# Create custom configuration
config = ClientConfig(api_base_url="https://custom-api.example.com")

# Create client
client = CommandGenerationClient(config)

# Generate a command
response = client.generate_command(
    query="list all files in the current directory",
    context={
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }
)

# Check for errors
if response.error:
    print(f"Error: {response.error}")
else:
    print(f"Command: {response.generated_command.command}")
    print(f"Explanation: {response.generated_command.explanation}")
```

## Error Handling

The client handles various error scenarios:

- HTTP errors (e.g., 404, 500)
- Connection errors
- Invalid JSON responses

In all error cases, the client returns a `GenerateResponse` with an error message and a fallback command.

## Configuration

The client can be configured using environment variables:

- `WISH_API_BASE_URL`: Base URL of the wish-command-generation-api service (default: http://localhost:3000)
