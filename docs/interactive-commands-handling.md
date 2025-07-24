# Interactive Commands Handling

wish provides improved handling for interactive commands (SSH, MySQL, FTP, etc.) by displaying usage examples and guidance instead of attempting automatic execution.

## Background

Previous implementations attempted to execute interactive commands using PTY, which had several issues:

- Complexity of PTY management
- Compatibility issues with environments like tmux
- Difficulty automating interactive operations
- Security concerns

## New Approach

When interactive commands are detected, wish displays:

1. **Command Information**: Command details and purpose
2. **Usage Examples**: Common usage patterns
3. **Execution Guide**: Manual execution steps
4. **Tips**: Command-specific best practices

## Interactive Commands List

The following commands are treated as interactive:

- `ftp`, `telnet`, `ssh`, `sftp`
- `msfconsole`
- `nc`, `ncat`, `socat`
- `mysql`, `psql`, `redis-cli`, `mongo`, `sqlite3`
- `python`, `python3`, `ipython`, `irb`, `node`, `ghci`, `erl`, `iex`

## Implementation Example

### Handling Mixed Plans

```python
# When a plan contains both interactive and non-interactive commands
plan = Plan(
    steps=[
        PlanStep(tool_name="nmap", command="nmap -sV target"),  # Non-interactive
        PlanStep(tool_name="ssh", command="ssh user@target"),   # Interactive
    ]
)

# Runtime behavior:
# 1. nmap command executes normally
# 2. ssh command displays examples and guidance
```

### Example Information Display

For SSH commands:

```
Interactive Command Information
Command: ssh user@192.168.1.1
Type: SSH client
Purpose: Connect to SSH service

Common Usage Patterns:
  • ssh user@hostname
  • ssh -p 2222 user@hostname  # Custom port
  • ssh -i keyfile user@hostname  # With key file
  • ssh -D 1080 user@hostname  # Dynamic port forwarding

To execute this command manually:
1. Open a new terminal window
2. Run: ssh user@192.168.1.1
3. Interact with the tool as needed
4. Return to wish when done

Tips:
  💡 Use -v for verbose output to debug connection issues
  💡 Add 'StrictHostKeyChecking no' to ~/.ssh/config for testing
  💡 Use ssh-keygen to generate key pairs for passwordless authentication
```

## Knowledge Base Integration

When possible, relevant usage examples are retrieved from the HackTricks knowledge base, allowing users to learn advanced command usage patterns.

## Benefits

1. **Educational Value**: Users can learn command usage patterns
2. **Flexibility**: Users can execute commands at their own timing
3. **Safety**: Prevents unexpected behavior from automatic execution
4. **Compatibility**: Avoids PTY-related issues

## Testing

The new functionality is covered by:

- `test_interactive_command_examples.py`: Unit tests
- `test_interactive_handling.py`: Integration test demo

## Future Extensions

- Support for more commands
- Dynamic example generation based on context
- User feedback collection and improvements