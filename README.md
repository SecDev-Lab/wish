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
- **Knowledge Base Management**: Load and manage knowledge bases from GitHub repositories for enhanced command suggestions

## Installation & Configuration

For detailed installation and configuration instructions, see the [Setup Guide](docs/setup.md).

Quick start:

```bash
pip install wish-sh
export OPENAI_API_KEY=your-api-key-here
wish  # or wish-sh on macOS
```

## Documentation

- [Setup Guide](docs/setup.md) - Installation and configuration
- [Basic Usage Guide](docs/usage-01-basic.md) - Getting started with wish-sh
- [Knowledge Loader Guide](docs/usage-02-knowledge-loader.md) - Enhancing wish-sh with domain knowledge
- [Command and Control (C2) Guide](docs/usage-03-C2.md) - Advanced operations for target systems
- [Design Documentation](docs/design.md) - Technical architecture and design

## Development

Refer to the README.md in each package `wish-*/`.

For contribution guidelines, including how to update the CHANGELOG and release process, see [Contributing Guidelines](CONTRIBUTING.md).

## License

[GNU Affero General Public License v3.0](LICENSE)
