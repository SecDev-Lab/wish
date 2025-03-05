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
import asyncio
from wish_command_execution import CommandExecutor
from wish_command_execution.backend import BashBackend

async def main():
    # Create a backend
    backend = BashBackend()
    
    # Create a command executor
    executor = CommandExecutor(backend)
    
    # Execute a command
    result = await executor.execute_command("ls -la")
    
    # Print the result
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.stdout}")

asyncio.run(main())
```

### Using Different Backends

```python
from wish_command_execution.backend import create_backend
from wish_command_execution.models import BashConfig, SliverConfig

# Using Bash backend
config = BashConfig(shell_path="/bin/bash")
backend = create_backend(config)

# Using Sliver backend
config = SliverConfig(
    session_id="your-session-id",
    client_config_path="/path/to/sliver/config"
)
backend = create_backend(config)
```
