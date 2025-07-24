# Contributing to wish

Thank you for your interest in contributing to wish! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key (for AI functionality testing)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SecDev-Lab/wish.git
   cd wish
   ```

2. **Install dependencies**
   ```bash
   uv sync --all-packages --dev
   ```

3. **Set up environment**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

4. **Verify installation**
   ```bash
   uv run wish --version
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific package tests
cd packages/wish-cli && uv run pytest

# Run E2E tests
uv run pytest e2e-tests/
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run type checking
uv run mypy packages/
```

### Project Structure

```
wish/
├── packages/           # Package modules
│   ├── wish-models/   # Core data models
│   ├── wish-core/     # Business logic
│   ├── wish-ai/       # LLM integration
│   ├── wish-tools/    # Tool integrations
│   ├── wish-knowledge/# Knowledge base
│   ├── wish-c2/       # C2 framework support
│   └── wish-cli/      # Main CLI application
├── docs/              # Documentation
├── e2e-tests/         # End-to-end tests
└── tmp/               # Temporary files (ignored)
```

## Contributing Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public functions and classes
- Keep line length to 120 characters maximum

### Commit Messages

Use conventional commit format:
```
type(scope): description

feat(cli): add new slash command for host enumeration
fix(models): resolve validation error for CIDR notation
docs(readme): update installation instructions
test(ai): add unit tests for plan generation
```

### Pull Request Process

1. **Fork the repository** and create your feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for new functionality

4. **Update documentation** if needed

5. **Run the full test suite**
   ```bash
   make test
   make lint
   ```

6. **Commit your changes** using conventional commit format

7. **Push to your fork** and create a pull request

### Pull Request Requirements

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated (if applicable)
- [ ] Commit messages follow conventional format
- [ ] Changes are described clearly in PR description

## Types of Contributions

### Bug Reports

When reporting bugs, please include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, wish version)
- Relevant logs or error messages

### Feature Requests

For feature requests, please provide:
- Clear description of the feature
- Use case and motivation
- Proposed implementation approach (if any)
- Any relevant examples or mockups

### Code Contributions

We welcome contributions for:
- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test coverage improvements

### Documentation

Help improve our documentation by:
- Fixing typos or grammatical errors
- Adding examples and use cases
- Improving clarity of existing content
- Translating documentation

## Development Guidelines

### Adding New Features

1. **Design first**: Discuss major changes in an issue before implementation
2. **Start small**: Break large features into smaller, manageable pieces
3. **Test thoroughly**: Include unit tests, integration tests, and documentation
4. **Follow patterns**: Use existing code patterns and architecture

### Package-Specific Guidelines

- **wish-models**: Focus on data validation and serialization
- **wish-core**: Implement business logic and state management
- **wish-ai**: Handle LLM interactions and prompt engineering
- **wish-tools**: Add tool integrations and output parsers
- **wish-knowledge**: Manage knowledge base and RAG functionality
- **wish-c2**: Implement C2 framework connectors
- **wish-cli**: Handle user interface and interaction logic

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check the `docs/` directory for detailed guides

## License

By contributing to wish, you agree that your contributions will be licensed under the GNU Affero General Public License v3.0.

## Recognition

Contributors are recognized in our releases and documentation. Thank you for helping make wish better!