# wish - LLM-assisted shell for penetration testing

[![PyPI version](https://img.shields.io/pypi/v/wish-sh.svg)](https://pypi.org/project/wish-sh)

## Overview

wish-sh is an LLM-assisted shell that helps users execute commands by translating natural language "wishes" into executable shell commands. It provides a user-friendly TUI (Text-based User Interface) for reviewing suggested commands, executing them, and monitoring their execution status.

![Screenshot of wish-sh](docs/images/screenshot.png)

## Features

- **Natural Language Command Generation**: Input your wishes in natural language and get executable commands
- **Command Suggestion and Confirmation**: Review suggested commands before execution
- **Real-time Status Monitoring**: Track command execution status in real-time
- **Command History**: Access and reuse previous commands
- **TUI Interface**: User-friendly terminal interface built with Textual

## Installation

```bash
pip install wish-sh
```

## Configuration

To use wish, you need to set up the following environment variables:

1. Create a `.env` file in your project directory (you can copy `.env.example` as a starting point)
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

## Usage

To start the wish shell:

```bash
wish
```

### Basic Commands

- Enter your wish in natural language
- Review the suggested commands
- Confirm to execute or reject to modify
- Monitor execution status
- Access command history with arrow keys

## Architecture

wish-sh is composed of four main packages:

1. **wish-models**: Core data models and structures
2. **wish-command-generation**: Command generation using LLM and RAG
3. **wish-command-execution**: Command execution and status tracking
4. **wish-sh**: TUI interface and user interaction

For detailed design documentation, see [Design Documentation](docs/design.md).

## Development

Refer to the README.md in each package `wish-*/`.

### Release

Use GitHub Actions UI: <https://github.com/SecDev-Lab/wish/actions/workflows/publish.yml>.

## License

[GNU Affero General Public License v3.0](LICENSE)
