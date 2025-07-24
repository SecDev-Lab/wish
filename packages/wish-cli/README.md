# wish-cli

**Main CLI Application for wish**

wish-cli is the main CLI application for the wish AI command center. It provides a refined UI experience similar to Claude Code, accelerating penetration testers' thought processes.

## 🚀 Quick Start

### Installation (Production)

```bash
pip install wish-sh
wish
```

### Development Environment

```bash
# In the project root
uv sync --all-packages --dev
uv run wish
```

## 🎯 Key Features

### ✨ Claude Code-style UI Experience
- Beautiful themes with Rich Console
- Interactive modals with Textual
- Asynchronous progress display
- Intuitive command completion

### 🔄 Hybrid Command Processing
- **Slash commands**: `/help`, `/status`, `/mode`, etc.
- **Natural language processing**: Instructions like "scan the target"
- **AI plan generation**: Context-aware execution plans
- **Plan approval flow**: Safe execution confirmation

### 🎨 Rich UI Elements
- Hierarchical status display
- Real-time job management
- Interactive plan editing
- Responsive progress display

## 📋 Command Reference

### Slash Commands

#### Basic Information
```bash
/help                    # Display help
/status                  # Display engagement status
/mode [recon|enum|exploit|report]  # Display/change mode
```

#### State Management
```bash
/scope add <target>      # Add target scope
/scope remove <target>   # Remove target scope
/scope                   # Display current scope
```

#### Results Display
```bash
/findings               # List findings
/jobs                   # List running jobs
/logs <job_id>          # Display job logs
```

#### Job Management
```bash
/stop <job_id>          # Stop job
/clear                  # Clear screen
/history                # Command history
```

### Natural Language Commands

```bash
# Reconnaissance Phase
scan the target
find active hosts
enumerate web directories

# Validation Phase
check for vulnerabilities
test for SQL injection
brute force login

# Exploitation Phase
escalate privileges
deploy sliver implant
```

## 🎮 User Interface

### Main Screen Layout

```
╭────────────────────────────────────────────────────────────────╮
│ ✻ Welcome to wish! - The Pentester's Command Center            │
│   /help for commands, /mode for current mode                   │
╰────────────────────────────────────────────────────────────────╯

[Output Area: Scrollable main display]
- AI responses and plan display
- Tool execution results
- Asynchronous notifications

╭──────────────────────────────────────────────────────────────╮
│ > your command here                                          │
╰──────────────────────────────────────────────────────────────╯
Mode: [recon] | Targets: [3] | Jobs: [1] | Press ? for help
```

### Plan Approval Flow

```
● I will scan the target at 10.0.0.5 for vulnerabilities.

● Execute(nikto)
  ⎿ Command: nikto -h 10.0.0.5 -p 80
  ⎿ Purpose: Web vulnerability scanning
  ⎿ Expected: HTTP service vulnerabilities

╭──────────────────────────────────────────────────────────────╮
│ Would you like to proceed?                                   │
│ ❯ 1. Yes (Execute Plan)                                     │
│   2. Edit Command                                           │
│   3. No (Cancel)                                            │
╰──────────────────────────────────────────────────────────────╯
```

## ⚙️ Configuration

### OpenAI API Key Setup

```bash
# Environment variable (recommended)
export OPENAI_API_KEY="your-openai-api-key-here"

# Configuration file
wish-ai-validate --init-config
wish-ai-validate --set-api-key "your-key"

# Manual configuration
echo 'api_key = "your-key"' >> ~/.wish/config.toml
```

### UI Customization

```toml
# ~/.wish/config.toml
[ui]
theme = "dark"              # dark/light
progress_style = "modern"   # modern/classic
auto_approve = false        # Auto-approve plans
max_history = 100          # Command history retention
```

## 🛠️ Development

### Architecture Overview

```
wish-cli/
├── main.py                 # Entry point
├── cli.py                  # Main CLI loop
├── ui/                     # UI-related
│   ├── ui_manager.py       # Rich+Textual integration
│   ├── progress_manager.py # Progress display
│   ├── textual_widgets.py  # Modal UI
│   └── input_handler.py    # Input handling
├── core/                   # Core functionality
│   └── command_dispatcher.py # Command routing
└── commands/               # Command implementations
    └── slash_commands.py   # Slash commands
```

### Key Components

#### WishCLI
Main CLI application class
- Asynchronous main loop
- Session management
- Graceful shutdown

#### UIManager
UI integration management class
- Rich Console + Textual integration
- Progress display
- Modal management

#### CommandDispatcher
Command routing class
- Slash command processing
- Natural language parsing
- AI plan execution

### Testing

```bash
# Unit tests
uv run pytest tests/

# E2E tests
uv run pytest e2e-tests/

# Component integration tests
uv run pytest e2e-tests/component/

# Workflow tests
uv run pytest e2e-tests/workflows/
```

### Code Quality

```bash
# Format code
uv run ruff format src/

# Lint code
uv run ruff check src/

# Type checking
uv run mypy src/
```

## 🔧 Troubleshooting

### Common Issues

#### "No module named 'wish_cli'"
```bash
# Run in development environment
uv run wish

# Or install package
pip install -e .
```

#### "OpenAI API key not configured"
```bash
# Set environment variable
export OPENAI_API_KEY="your-key"

# Verify configuration
wish-ai-validate --check-env
```

#### "Rich/Textual import errors"
```bash
# Reinstall dependencies
uv sync --reinstall
```

### Performance Tips

- **Memory usage**: Reduce logs with `--log-level ERROR`
- **Response speed**: Speed up with proper API key configuration
- **CPU usage**: Adjust number of concurrent jobs

## 🤝 Contributing

### Development Setup

```bash
# 1. Fork and clone
git clone your-fork-url
cd wish/.sprout/wish-cli-basic-ui

# 2. Set up development environment
uv sync --all-packages --dev

# 3. Pre-checks
make lint
make test

# 4. Implement and test
# ... your changes ...

# 5. Quality checks
make format
make test
```

### Code Style

- **Python**: PEP 8 compliant, ruff formatting
- **Type Hints**: Required (mypy checks)
- **Docstrings**: Google style
- **Error Handling**: Fail-fast principle

## 📄 License

MIT License - See LICENSE file for details.

## 🔗 Links

- [Project Homepage](https://github.com/SecDev-Lab/wish)
- [Documentation](https://docs.wish.dev)
- [Issue Tracker](https://github.com/SecDev-Lab/wish/issues)
- [Contributing Guide](CONTRIBUTING.md)