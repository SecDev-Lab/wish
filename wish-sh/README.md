# wish-sh

[![PyPI version](https://img.shields.io/pypi/v/wish-sh.svg)](https://pypi.org/project/wish-sh)

## Development

### Environment Setup

To use this package, you need to set up the following environment variables:

1. Create a `.env` file (you can copy `.env.example` as a starting point)
2. Configure the required environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `OPENAI_MODEL`: The OpenAI model to use (default: gpt-4o)
   - `WISH_HOME`: The directory where wish will store its data (default: ~/.wish)

Example:

```bash
# .env file
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
WISH_HOME=~/.wish
```

### Running the TUI

```bash
uv sync --dev
uv run wish
```

## Documentation

- [TUI Design Documentation](docs/design.md) - Detailed explanation of the TUI implementation
