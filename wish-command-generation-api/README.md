# wish-command-generation-api

A serverless application that provides both an API and a library for generating shell commands.

## Project Overview

This project receives user queries, generates appropriate shell commands using a LangGraph processing flow, and returns the results via an API or library interface.

### Main Features

- Shell command generation (using OpenAI language models)
- Context-aware command suggestions
- Generation and return of command results

### Project Structure

- `src/wish_command_generation_api` - Lambda function code for the application
  - `app.py` - Lambda handler
  - `config.py` - Configuration class
  - `core/` - Core functionality
    - `generator.py` - Command generation function
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
   - `WISH_API_BASE_URL`: Base URL of the wish-command-generation-api service (default: http://localhost:3000)

Example:

```
# OpenAI API settings
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o

# API settings
WISH_API_BASE_URL=http://localhost:3000
```

### RAG Configuration

The command generation API uses Retrieval-Augmented Generation (RAG) to improve command suggestions. By default, it uses ChromaDB as the vector store, but you can also configure it to use Qdrant:

- `VECTOR_STORE_TYPE`: Vector store type to use (default: "chroma", options: "chroma" or "qdrant")
- `EMBEDDING_MODEL`: OpenAI embedding model to use (default: text-embedding-3-small)

#### Qdrant Configuration (Optional)

If you want to use Qdrant as the vector store, set the following environment variables:

- `QDRANT_HOST`: Qdrant server host (default: localhost)
- `QDRANT_PORT`: Qdrant server port (default: 6333)
- `QDRANT_COLLECTION_HACKTRICKS`: Qdrant collection name (default: hacktricsk)

Example:

```
# RAG settings
VECTOR_STORE_TYPE=qdrant
EMBEDDING_MODEL=text-embedding-3-small

# Qdrant settings
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_HACKTRICKS=hacktricks
```

Environment variables are automatically loaded from the `~/.wish/env` file and passed to the SAM local container.

The client will automatically append the `/generate` endpoint to the base URL.

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

### Graph Visualization

The command generation graph can be visualized using the following command:

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
curl -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "list all files in the current directory",
    "context": {
      "current_directory": "/home/user",
      "history": ["cd /home/user", "mkdir test"]
    }
  }'
```

#### API Response Example

```json
{
  "generated_command": {
    "command": "ls -la",
    "explanation": "This command lists all files in the current directory, including hidden files, with detailed information."
  }
}
```

### Using as a Library

#### Installation

The package can be installed with different vector store backends:

```bash
# Basic installation (no vector stores)
pip install git+https://github.com/SecDev-Lab/wish-command-generation-api.git

# With ChromaDB support (default vector store)
pip install "git+https://github.com/SecDev-Lab/wish-command-generation-api.git#egg=wish-command-generation-api[chroma]"

# With Qdrant support
pip install "git+https://github.com/SecDev-Lab/wish-command-generation-api.git#egg=wish-command-generation-api[qdrant]"
```

Note that you must install the appropriate dependencies for the vector store you want to use. If you try to use a vector store without installing its dependencies, the system will display an error message with installation instructions.

#### Basic Usage

```python
from wish_command_generation_api.core.generator import generate_command
from wish_command_generation_api.models import GenerateRequest
from wish_command_generation_api.config import GeneratorConfig

# Create request
request = GenerateRequest(
    query="list all files in the current directory",
    context={
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }
)

# Run generation with default configuration (loads from environment variables)
response = generate_command(request)

# Or run generation with custom configuration
config = GeneratorConfig(
    openai_api_key="your-api-key-here",
    openai_model="gpt-4o"
)
response = generate_command(request, config=config)

# Get results
generated_command = response.generated_command
print(f"Command: {generated_command.command}")
print(f"Explanation: {generated_command.explanation}")
```

#### Advanced Usage

```python
from wish_command_generation_api.graph import create_command_generation_graph
from wish_command_generation_api.models import GraphState
from wish_command_generation_api.config import GeneratorConfig

# Create custom configuration
config = GeneratorConfig(
    openai_model="gpt-4o",
    langchain_tracing_v2=True
)

# Create graph directly
graph = create_command_generation_graph(config=config)

# Create initial state
initial_state = GraphState(
    query="list all files in the current directory",
    context={
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }
)

# Run graph
result = graph.invoke(initial_state)

# Get results
generated_command = result.generated_command
```

#### Using with Qdrant

To use Qdrant as the vector store:

```python
from wish_command_generation_api.config import GeneratorConfig

# Create configuration with Qdrant
config = GeneratorConfig(
    vector_store_type="qdrant",
    qdrant_host="localhost",
    qdrant_port=6333,
    qdrant_collection_HACKTRICKS="wish"
)

# Use this config with the generator
response = generate_command(request, config=config)
```

Note: Make sure you have installed the package with Qdrant support as described in the Installation section.
