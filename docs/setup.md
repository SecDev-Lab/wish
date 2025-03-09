# Setup Guide

This guide explains how to install and set up `wish-sh` and `wish-knowledge-loader`.

## Prerequisites

- Python 3.13 or higher
- OpenAI API key (available from the [OpenAI website](https://platform.openai.com/))

## wish-sh

### Installation

Install wish-sh using the following command:

```bash
pip install wish-sh
```

### Environment Variables

To use wish-sh, you need to set the following environment variables:

```bash
# Required: Set your OpenAI API key
export OPENAI_API_KEY=your-api-key-here

# Optional: Set the OpenAI model to use (default: gpt-4o)
export OPENAI_MODEL=gpt-4o

# Optional: Set the wish home directory (default: ~/.wish)
export WISH_HOME=~/.wish

# Optional: Set a custom .env file path (default: $WISH_HOME/env)
# This is used by all wish packages
export WISH_ENV_FILE=/path/to/your/custom/.env
```

You can add these environment variables to your shell configuration file (like `.bashrc` or `.zshrc`) to have them automatically set when you open a terminal.

### Using .env File

Instead of setting environment variables directly, you can use a `.env` file. The default location for this file is `$WISH_HOME/env`. Here's how to set it up:

1. Make sure the `$WISH_HOME` directory exists:

```bash
mkdir -p ~/.wish
```

2. Copy the example `.env` file to `$WISH_HOME/env`:

```bash
cp .env.example ~/.wish/env
```

3. Edit the `$WISH_HOME/env` file to set your actual API keys and other settings:

```bash
nano ~/.wish/env
```

The `.env` file should contain settings like:

```
# Wish home directory
WISH_HOME=~/.wish

# OpenAI API settings
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
# Required for wish-knowledge-loader
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# LangSmith settings (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=wish
```

Make sure to replace `your-api-key-here` with your actual OpenAI API key, and if you're using LangSmith, replace `your-langsmith-api-key-here` with your actual LangSmith API key.

### Verifying Installation

After installation and environment variable setup, you can start wish-sh with:

```bash
wish
```

**Note for macOS users**: macOS includes a built-in `wish` command as part of the Tcl/Tk package. To avoid conflicts, you can use the alternative command:

```bash
wish-sh
```

Both commands provide identical functionality.

You can also specify a custom .env file path using the `--env-file` option:

```bash
wish --env-file /path/to/your/custom/.env
# or on macOS
wish-sh --env-file /path/to/your/custom/.env
```

## wish-knowledge-loader

### Installation

Install wish-knowledge-loader using the following command:

```bash
pip install wish-knowledge-loader
```

### Environment Variables

wish-knowledge-loader uses the same environment variables as wish-sh (`OPENAI_API_KEY` is required, while `OPENAI_MODEL` and `WISH_HOME` are optional).

Additionally, when using wish-knowledge-loader, you need to set the following environment variable:

```bash
# Required for wish-knowledge-loader: Set the OpenAI embedding model
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

This variable is specifically required for the knowledge loader functionality, as it needs to generate embeddings for the documents.

### Verifying Installation

After installation, you can verify that wish-knowledge-loader is working correctly by running:

```bash
wish-knowledge-loader --help
```

You should see a help message similar to:

```
Usage: wish-knowledge-loader [OPTIONS]

Options:
  --repo-url TEXT    GitHub repository URL to clone
  --glob TEXT        Glob pattern for files to include
  --title TEXT       Title for the knowledge base
  --help             Show this message and exit.
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   
   ```
   Error: OpenAI API key not found
   ```
   
   Solution: Ensure that the `OPENAI_API_KEY` environment variable is correctly set.

2. **Model Error**
   
   ```
   Error: The model 'xxx' does not exist
   ```
   
   Solution: Ensure that the `OPENAI_MODEL` environment variable is set to a valid OpenAI model name.

3. **Python Version Error**
   
   ```
   Error: Python 3.13 or higher is required
   ```
   
   Solution: Ensure that Python 3.13 or higher is installed.

4. **Embedding Model Error**
   
   ```
   Error: You are not allowed to generate embeddings from this model
   ```
   
   Solution: Ensure that the `OPENAI_EMBEDDING_MODEL` environment variable is set to a valid OpenAI embedding model (e.g., text-embedding-3-small) when using wish-knowledge-loader.

## Next Steps

Now that you have installed and set up wish-sh and wish-knowledge-loader, you can:

- Learn how to use wish-sh with the [Basic Usage Guide](usage-01-basic.md)
- Explore how to enhance wish-sh with [Knowledge Bases](usage-02-knowledge-loader.md)
- Learn about [Command and Control (C2) for Target System Operations](usage-03-C2.md)
