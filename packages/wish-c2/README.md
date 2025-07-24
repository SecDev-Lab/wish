# wish-c2

C2 framework connectors for wish.

## Overview

The `wish-c2` package provides connectors for integrating Command and Control (C2) frameworks with wish. Currently supports Sliver C2 with multiple modes of operation.

## Features

- **Mock Mode**: Demo and testing mode with realistic responses
- **Real Mode**: Actual Sliver C2 server integration via gRPC
- **Safe Mode**: Sandboxed execution with security restrictions
- **Factory Pattern**: Easy connector creation based on configuration
- **Security Features**: Command filtering, path blocking, read-only mode

## Installation

```bash
pip install wish-c2
```

## Quick Start for End Users

### Step 1: Install and Run Sliver Server
```bash
# Install Sliver (requires root/sudo)
curl https://sliver.sh/install|sudo bash

# Start server in background
sliver-server daemon
```

### Step 2: Generate Configuration
```bash
# Create operator config for your user
sliver-server operator --name $USER --lhost localhost --save ~/.sliver-client/configs/wish.cfg
```

**Note**: This config file contains certificates that authenticate you to the Sliver server. 
Keep it secure and regenerate if the server is reinstalled.

### Step 3: Configure wish
Add to `~/.wish/config.toml`:
```toml
[c2.sliver]
enabled = true
mode = "real"
config_path = "~/.sliver-client/configs/wish.cfg"
```

### Step 4: Test Connection
```bash
wish
# In wish shell:
/sliver status
```

### Certificate Troubleshooting
If you see SSL certificate errors, your config file likely doesn't match the server.
Generate a new one with Step 2 above. See the [Sliver Setup Guide](../../docs/sliver-setup-guide.md) for detailed troubleshooting.

## Usage

### Basic Usage

```python
from wish_c2 import create_c2_connector

# Create mock connector (default)
connector = create_c2_connector("sliver", mode="mock")

# Connect to C2 server
await connector.connect()

# Get active sessions
sessions = await connector.get_sessions()
for session in sessions:
    print(f"{session.name} - {session.host} ({session.user})")

# Execute command
result = await connector.execute_command(session.id, "whoami")
print(result.stdout)

# Disconnect
await connector.disconnect()
```

### Configuration-based Usage

```python
from wish_c2 import get_c2_connector_from_config

config = {
    "c2": {
        "sliver": {
            "enabled": True,
            "mode": "real",
            "config_path": "~/.sliver-client/configs/wish.cfg"
        }
    }
}

connector = get_c2_connector_from_config(config)
```

## Configuration

### Environment Variables

- `WISH_C2_MODE`: Connector mode (mock/real/safe)
- `WISH_C2_SLIVER_CONFIG`: Path to Sliver config file
- `WISH_C2_SLIVER_SERVER`: Override server address
- `WISH_C2_SANDBOX`: Enable sandbox mode (true/false)
- `WISH_C2_READONLY`: Enable read-only mode (true/false)
- `WISH_C2_SLIVER_SKIP_VERIFY`: Skip SSL certificate verification (true/false)
- `WISH_C2_SLIVER_CA_CERT`: Path to custom CA certificate file

### Configuration File

```toml
# ~/.wish/config.toml

[c2.sliver]
enabled = true
mode = "mock"  # mock | real | safe

# For real mode
[c2.sliver.real]
mode = "real"
config_path = "~/.sliver-client/configs/wish.cfg"

# SSL options (optional)
[c2.sliver.real.ssl_options]
skip_verify = false  # Set to true only for development
# ca_cert_path = "/path/to/ca.crt"
# target_name_override = "sliver.local"

# For safe mode with restrictions
[c2.sliver.safe]
mode = "safe"
config_path = "~/.sliver-client/configs/wish.cfg"
sandbox_mode = true
read_only = false
allowed_commands = ["ls", "pwd", "whoami", "id", "cat", "ps", "netstat"]
blocked_paths = ["/etc/shadow", "/etc/passwd", "/root/.ssh"]
max_file_size = 10485760  # 10MB

# SSL options for safe mode (optional)
[c2.sliver.safe.ssl_options]
skip_verify = false
```

## Connector Modes

### Mock Mode
- Default mode for demos and testing
- No actual C2 server required
- Provides realistic responses for common commands
- Includes demo session "FANCY_TIGER" for HTB Lame scenario

### Real Mode
- Connects to actual Sliver C2 server via gRPC
- Requires `sliver-py` package and valid Sliver configuration
- Full functionality including command execution and shell sessions

### Safe Mode
- Wraps real connector with security restrictions
- Command filtering and validation
- Path blocking for sensitive files
- Optional read-only mode
- Command whitelisting

## Security Features

### Command Filtering
- Blocks dangerous commands (rm -rf /, fork bombs, etc.)
- Prevents command injection attempts
- Validates paths against blocklist

### Sandbox Mode
When enabled, enforces:
- Dangerous command pattern detection
- Path access restrictions
- Command injection prevention

### Read-Only Mode
Prevents all write operations including:
- File modifications
- System configuration changes
- Process termination

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific test
PYTHONPATH=src uv run pytest tests/test_factory.py -v
```

### Adding New C2 Frameworks

1. Create new connector class inheriting from `BaseC2Connector`
2. Implement required methods: `connect()`, `disconnect()`, `get_sessions()`, `execute_command()`, `start_interactive_shell()`
3. Add to factory pattern in `factory.py`
4. Write tests for new connector

## Troubleshooting

### SSL Certificate Verification Errors

If you encounter SSL certificate verification errors when connecting to Sliver C2 server, try these solutions:

#### Solution 1: Use Environment Variables (Recommended)

Set environment variables to handle SSL configuration:

```bash
# Skip SSL verification (development only - insecure!)
export WISH_C2_SLIVER_SKIP_VERIFY=true

# Or use custom CA certificate
export WISH_C2_SLIVER_CA_CERT=/path/to/sliver-ca.crt
```

#### Solution 2: Configuration-based SSL Options

```python
connector = create_c2_connector(
    "sliver",
    mode="real",
    config={
        "config_path": "~/.sliver-client/configs/default.cfg",
        "ssl_options": {
            "skip_verify": True,  # WARNING: Only for development!
            # "ca_cert_path": "/path/to/ca.crt",  # Alternative: custom CA
            # "target_name_override": "sliver.local"  # If CN doesn't match hostname
        }
    }
)
```

#### Solution 3: System Certificate Store

Add the Sliver server's certificate to your system's trusted certificate store:

```bash
# Linux (Ubuntu/Debian)
sudo cp sliver-server.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain sliver-server.crt

# Windows
certlm.msc  # Add to "Trusted Root Certification Authorities"
```

#### Diagnosis Commands

To debug SSL certificate issues:

```bash
# Check certificate details
openssl s_client -connect localhost:31337 -servername localhost -showcerts

# Verify certificate chain
openssl verify -CAfile /path/to/ca.crt /path/to/server.crt

# Test connection with curl
curl -k -v https://localhost:31337
```

**⚠️ Security Warning**: The `skip_verify` option disables SSL certificate validation entirely, making connections vulnerable to man-in-the-middle attacks. Only use this in development environments, never in production!

### Connection Issues
- Verify Sliver config file exists and is readable
- Check server address and port
- Ensure Sliver server is running and accessible
- Review SSL certificate configuration (see above)

### Permission Errors
- Config files should have restricted permissions (600)
- Check file ownership
- Ensure user has access to certificate files

### Command Execution Failures
- Verify session is active
- Check command syntax
- Review security restrictions in safe mode
- Ensure implant is responsive

## Testing

The package includes comprehensive tests for all components:

```bash
# Run all tests
pytest

# Run only unit tests (no Sliver server required)
pytest -m "not requires_sliver"

# Run specific test categories
pytest tests/test_factory.py         # Factory pattern tests
pytest tests/test_safety.py          # Safety features tests
pytest tests/test_interface_compatibility.py  # Interface tests

# Run real Sliver integration tests (requires Sliver server)
pytest -m "requires_sliver"          # Note: See limitations below
```

### Real Sliver Integration Tests

The real Sliver integration tests require:
1. A running Sliver C2 server on localhost:31337
2. A valid Sliver config file at `~/.sliver-client/configs/wish-test.cfg`

**⚠️ SSL Certificate Requirements**: 

The Sliver C2 server uses self-signed certificates for mTLS (mutual TLS) authentication. The client configuration file must contain certificates that match the running server instance.

#### Setting Up Test Configuration

1. **Generate a new operator config** (recommended):
   ```bash
   # On the machine running Sliver server
   sliver-server operator --name wish-test --lhost localhost --save wish-test.cfg
   
   # Copy to client configs directory
   cp wish-test.cfg ~/.sliver-client/configs/
   ```

2. **Use existing working config**:
   ```bash
   # If you have a working config (e.g., from sliver client)
   cp ~/.sliver-client/configs/your-working-config.cfg ~/.sliver-client/configs/wish-test.cfg
   ```

#### Common SSL Issues

- **"unable to get local issuer certificate"**: The config file certificates don't match the server
- **"certificate verify failed"**: The server was regenerated/restarted after config creation
- **Connection timeouts**: Firewall or server not running on expected port

#### Running Tests

```bash
# Run only unit tests (no Sliver server required)
pytest -m "not requires_sliver"

# Run real Sliver integration tests (requires server + valid config)
pytest -m "requires_sliver"
```

### Running Tests in CI/CD

For continuous integration environments, exclude real Sliver tests:

```bash
# GitHub Actions / GitLab CI example
pytest -m "not requires_sliver" --cov=src/wish_c2
```

## License

MIT
