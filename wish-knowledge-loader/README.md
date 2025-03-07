# wish-knowledge-loader

A CLI tool for loading knowledge bases into wish.

## Overview

`wish-knowledge-loader` is a command-line tool that clones GitHub repositories, extracts content from specified files, and stores them in a vector database for use with wish.

## Installation

```bash
# Install from the repository
cd wish-knowledge-loader
uv sync --dev

cp .env.example .env
vim .env  # Set the OpenAI API key
```

## Usage

```bash
# Basic usage
wish-knowledge-loader --repo-url https://github.com/username/repo --glob "**/*.md" --title "Knowledge Base Title"
```

### Options

- `--repo-url`: GitHub repository URL to clone
- `--glob`: Glob pattern for files to include (e.g., "**/*.md" for all Markdown files)
- `--title`: Title for the knowledge base

## Environment Variables

The following environment variables can be set in a `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: OpenAI embedding model to use (default: "text-embedding-3-small")
- `WISH_HOME`: Path to the wish home directory (default: "~/.wish")

## Development

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

## Verifying Search Functionality

After creating a knowledge base, you can verify the search functionality using the provided script:

```bash
# Set the OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Run the search script
python scripts/search_knowledge.py "Knowledge Base Title" "your search query"
```

The script will:

1. Load the vector store for the specified knowledge base
2. Search for documents similar to your query
3. Display the top 4 results with their content and metadata

You can adjust the number of results by modifying the `k` parameter in the script.
