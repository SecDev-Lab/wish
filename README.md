# wish

[![Tests](https://github.com/SecDev-Lab/wish/workflows/Tests/badge.svg)](https://github.com/SecDev-Lab/wish/actions/workflows/test.yml)
[![Code Quality](https://github.com/SecDev-Lab/wish/workflows/Code%20Quality/badge.svg)](https://github.com/SecDev-Lab/wish/actions/workflows/lint.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**AI-Powered Penetration Testing Command Center**

## Overview

wish is a workflow-aware AI command center designed to accelerate penetration testers' thinking and reduce context-switching costs.

## Installation

```bash
pip install wish-sh
```

## Setup

### OpenAI API Key Configuration

wish requires an OpenAI API key for AI functionality. Configure it using one of these methods:

**Option 1: Configuration File (Recommended)**
```bash
# Initialize configuration file
wish-ai-validate --init-config

# Set your API key
wish-ai-validate --set-api-key "your-openai-api-key-here"
```

**Option 2: Environment Variable**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Option 3: Manual Configuration**
Edit `~/.wish/config.toml`:
```toml
[llm]
api_key = "your-openai-api-key-here"
model = "gpt-4o"
```

### Getting an OpenAI API Key

1. Visit [OpenAI API Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Go to "API Keys" section
4. Click "Create new secret key"
5. Copy the generated key and set it as shown above

⚠️ **Important**: Keep your API key secure and never commit it to version control.

## Usage

```bash
wish
# or ...
wish-sh
```

> **Note**: On first launch, wish will download and index the HackTricks knowledge base. This may take a few minutes but only happens once.

### Verifying Setup

To verify your API key is configured correctly:

**Option 1: Using wish-ai validation tool**
```bash
# Install wish-ai package and run validation
pip install ./packages/wish-ai
wish-ai-validate
```

**Option 2: Using main application**
```bash
# The application will validate the API key on startup
wish --version
```

If you see authentication errors, double-check your OPENAI_API_KEY environment variable.

## Development

### Quick Start (Development Environment)

```bash
# 1. Clone and navigate to the project
git clone <repository-url>
cd wish

# 2. Install dependencies
uv sync --all-packages --dev

# 3. Set up OpenAI API key
export OPENAI_API_KEY="your-openai-api-key-here"

# 4. Run wish-cli directly
uv run wish
```

### Development Commands

```bash
# Setup development environment
make dev-setup

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Run specific package tests
cd packages/wish-cli && uv run pytest

# Run E2E tests
uv run pytest e2e-tests/
```

### Package Development

```bash
# Work on specific package
cd packages/wish-cli

# Install package in development mode
uv sync --dev

# Run package-specific tests
uv run pytest tests/

# Build package
uv build
```

## Troubleshooting

### Common Issues

#### "No module named 'wish_cli'" in Development
```bash
# Solution: Use uv run instead of direct execution
uv run wish

# Or install in development mode
pip install -e .
```

#### OpenAI API Authentication Errors
```bash
# Check your API key is set
echo $OPENAI_API_KEY

# Verify API key configuration
wish-ai-validate --check-env

# Re-initialize configuration
wish-ai-validate --init-config
wish-ai-validate --set-api-key "your-key-here"
```

#### Import or Dependency Issues
```bash
# Reinstall all dependencies
uv sync --reinstall --all-packages --dev

# Clear uv cache
uv cache clean

# Check Python version (requires 3.11+)
python --version
```

#### Development Environment Setup
```bash
# Ensure you're in the correct directory
cd wish

# Install all workspace packages
uv sync --all-packages --dev

# Verify installation
uv run python -c "import wish_cli; print('✅ Installation successful')"
```

### Performance Issues

#### Slow Startup
- **Cause**: OpenAI API key validation
- **Solution**: Use cached configuration or environment variables

#### High Memory Usage
- **Cause**: Rich console history retention
- **Solution**: Limit history size in configuration

#### UI Responsiveness
- **Cause**: Blocking operations in main thread
- **Solution**: All operations are async by design

### Getting Help

- **GitHub Issues**: [Report bugs](https://github.com/SecDev-Lab/wish/issues)
- **Documentation**: Check `docs/` directory for detailed guides
- **Community**: Join our development discussions

## Sliver C2 Integration (Optional)

wish supports integration with Sliver C2 framework for post-exploitation workflows.

### Prerequisites
1. Sliver server installed and running
2. Valid operator configuration file
3. Active implants/beacons (for command execution)

See [Sliver Setup Guide](docs/sliver-setup-guide.md) for detailed instructions.

## Packages

- **wish-models**: Core data models and validation
- **wish-core**: Business logic and state management  
- **wish-ai**: LLM integration and plan generation
- **wish-tools**: Tool integrations and parsers
- **wish-knowledge**: RAG and knowledge base integration
- **wish-c2**: C2 framework connectors
- **wish-cli**: Main CLI application

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

- 📋 [Code of Conduct](CODE_OF_CONDUCT.md)
- 🐛 [Report Issues](https://github.com/SecDev-Lab/wish/issues)
- 💡 [Request Features](https://github.com/SecDev-Lab/wish/issues/new)

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
