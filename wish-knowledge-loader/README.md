# wish-knowledge-loader

A CLI tool for loading knowledge bases into wish.

## Overview

`wish-knowledge-loader` is a command-line tool that clones GitHub repositories, extracts content from specified files, and stores them in a vector database for use with wish.

## Installation

```bash
# Install from the repository
cd wish-knowledge-loader
uv sync --dev
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
