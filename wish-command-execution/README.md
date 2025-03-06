# wish-command-execution

Command execution package for wish.

## Overview

`wish-command-execution` is a Python package that provides command execution functionality for the wish ecosystem. It allows executing commands on different backend shells (bash, Sliver C2, etc.) and tracking their execution status.

## Installation

```bash
pip install wish-command-execution
```

Or for development:

```bash
git clone https://github.com/SecDev-Lab/wish.git
cd wish/wish-command-execution
uv pip install -e .
```

## Usage

### Basic Usage

```python
from wish_models import Wish
from wish_command_execution import CommandExecutor
from wish_command_execution.backend import BashBackend

def main():
    # Create a wish
    wish = Wish.create("List files")
    
    # Create a backend
    backend = BashBackend()
    
    # Create a command executor
    executor = CommandExecutor(backend)
    
    # Execute a command
    cmd_num = 1
    executor.execute_command(wish, "ls -la", cmd_num)
    
    # Check running commands
    executor.check_running_commands()
    
    # Print the result when completed
    for result in wish.command_results:
        print(f"Command: {result.command}")
        print(f"Exit code: {result.exit_code}")
        print(f"State: {result.state}")

if __name__ == "__main__":
    main()
```

### Using Different Backends

```python
from wish_command_execution.backend import create_backend
from wish_command_execution.backend.factory import BashConfig, SliverConfig

# Using Bash backend with custom log summarizer
def my_log_summarizer(log_files):
    return "Custom log summary"

config = BashConfig(log_summarizer=my_log_summarizer)
backend = create_backend(config)

# Using Sliver backend (future implementation)
config = SliverConfig(
    session_id="your-session-id",
    client_config_path="/path/to/sliver/config"
)
backend = create_backend(config)  # Will raise NotImplementedError currently
```
