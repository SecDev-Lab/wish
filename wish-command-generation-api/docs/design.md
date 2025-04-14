# Command Generation Design

This document describes the design of the command generation system.

## Overview

The command generation system is designed to generate shell commands based on natural language queries. It uses a LangGraph processing flow to handle the generation process.

## Architecture

The system is built as a serverless API using AWS Lambda and API Gateway. The core functionality is implemented using LangGraph, which provides a flexible and extensible framework for building AI-powered applications.

## Graph Workflow

The command generation process follows these steps:

1. **Query Processing**: The user's natural language query is processed and normalized to make it more suitable for command generation.
2. **Command Generation**: The processed query is used to generate appropriate shell commands.
3. **Result Formatting**: The generated command is formatted with an explanation of what it does.

## Graph Visualization

![Command Generation Graph](graph.svg)

## Components

### Models

- **GraphState**: Represents the state of the LangGraph execution, containing input fields, intermediate results, and output fields.
- **GenerateRequest**: Represents a request to generate a command.
- **GenerateResponse**: Represents a response containing the generated command.
- **GeneratedCommand**: Represents a generated shell command with an explanation.

### Nodes

- **query_processor**: Processes and normalizes the user's query.
- **command_generator**: Generates shell commands based on the processed query.
- **result_formatter**: Formats the result with an explanation.

### Core

- **generator.py**: Main function for generating commands using the LangGraph flow.

## API

The API provides a single endpoint:

- **POST /generate**: Generates a shell command based on a natural language query.

### Request Format

```json
{
  "query": "list all files in the current directory",
  "context": {
    "current_directory": "/home/user",
    "history": ["cd /home/user", "mkdir test"]
  }
}
```

### Response Format

```json
{
  "generated_command": {
    "command": "ls -la",
    "explanation": "This command lists all files in the current directory, including hidden files, with detailed information."
  }
}
```

## Configuration

The system can be configured using environment variables:

- `OPENAI_API_KEY`: OpenAI API key for language model access.
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o).
- `LANGCHAIN_TRACING_V2`: Enable LangChain tracing (default: false).
- `LANGCHAIN_PROJECT`: LangChain project name (default: wish-command-generation-api).
