# Sliver C2 Setup Guide

This guide walks you through setting up Sliver C2 integration with wish.

## What is Sliver C2?

Sliver is an open-source Command and Control (C2) framework designed for security professionals. It provides:
- Cross-platform implant generation
- Secure communication channels
- Post-exploitation capabilities
- Team collaboration features

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows
- **Architecture**: x86_64 or ARM64
- **Privileges**: Root/Administrator access for server installation
- **Network**: Port 31337 (default) must be accessible

### Software Requirements
- Python 3.11 or higher
- wish installed (`pip install wish-sh`)

## Installing Sliver Server

### Option 1: Quick Install (Linux/macOS)
```bash
# Download and install (requires sudo/root)
curl https://sliver.sh/install|sudo bash
```

### Option 2: Manual Installation
1. Visit [Sliver Releases](https://github.com/BishopFox/sliver/releases)
2. Download the appropriate binary for your system
3. Extract and install:
   ```bash
   tar -xzf sliver-server_*.tar.gz
   sudo mv sliver-server /usr/local/bin/
   sudo chmod +x /usr/local/bin/sliver-server
   ```

## Starting Sliver Server

### Run as Daemon (Recommended)
```bash
# Start Sliver server in background
sliver-server daemon

# Verify it's running
ps aux | grep sliver-server
# Expected output: /usr/local/bin/sliver-server daemon
```

### Run Interactively (For Testing)
```bash
# Start with console interface
sliver-server
```

## Generating Operator Configuration

Operator configurations contain the certificates and connection details needed to connect to the Sliver server.

### Create Configuration for wish
```bash
# Generate a new operator configuration
sliver-server operator --name $USER --lhost localhost --save wish.cfg

# Create configs directory if it doesn't exist
mkdir -p ~/.sliver-client/configs

# Move configuration to standard location
mv wish.cfg ~/.sliver-client/configs/
```

### Configuration Parameters
- `--name`: Operator name (appears in logs)
- `--lhost`: Server address (use actual IP for remote access)
- `--save`: Output filename

## Understanding Certificates

### How Sliver Uses Certificates

Sliver implements mutual TLS (mTLS) authentication:
- **Server Certificate**: Identifies the Sliver server
- **Client Certificate**: Authenticates the operator
- **CA Certificate**: Validates both server and client

Each operator configuration file contains:
1. CA certificate (to verify server)
2. Client certificate (your identity)
3. Client private key (proves identity)

### Important Certificate Notes

⚠️ **Certificate Matching**: The operator configuration must match the server instance. If you see SSL errors, the certificates don't match.

⚠️ **Server Reinstalls**: If you reinstall Sliver server or regenerate its certificates, all existing operator configs become invalid.

⚠️ **Security**: Operator configs contain private keys. Treat them like passwords:
- Keep them secure (file permissions 600)
- Don't share them
- Generate unique configs per user

## Configuring wish

### Edit Configuration File

Add the following to `~/.wish/config.toml`:

```toml
[c2.sliver]
enabled = true
mode = "real"  # Use "real" for actual server, "mock" for testing
config_path = "~/.sliver-client/configs/wish.cfg"
```

### Configuration Options

```toml
[c2.sliver]
enabled = true
mode = "real"

# Optional: Override server settings
# server = "192.168.1.100:31337"  # Override config file server

# Optional: Safety features
[c2.sliver.safety]
sandbox_mode = true  # Enable command filtering
read_only = false    # Prevent write operations
allowed_commands = ["ls", "pwd", "whoami", "id", "ps"]
blocked_paths = ["/etc/shadow", "/root/.ssh"]
```

## Testing the Connection

### Step 1: Verify Configuration
```bash
# Check if config file exists and is readable
ls -la ~/.sliver-client/configs/wish.cfg
# Should show: -rw------- (permissions 600)
```

### Step 2: Test in wish
```bash
# Start wish
wish

# In the wish shell, check Sliver status
/sliver status
# Expected: "Connected to Sliver C2 server"

# List active sessions (if any)
/sliver sessions
```

### Step 3: Verify with Sliver Client (Optional)
```bash
# Use official Sliver client to verify server is accessible
sliver-client -c ~/.sliver-client/configs/wish.cfg
```

## Certificate Troubleshooting

### Common SSL/TLS Errors

#### "unable to get local issuer certificate"
**Cause**: The operator config doesn't match the running server.

**Solutions**:
1. Generate a new operator configuration:
   ```bash
   sliver-server operator --name $USER --lhost localhost --save new-config.cfg
   cp new-config.cfg ~/.sliver-client/configs/wish.cfg
   ```

2. Use an existing working configuration:
   ```bash
   # If you have a working Sliver client config
   cp ~/.sliver-client/configs/working-config.cfg ~/.sliver-client/configs/wish.cfg
   ```

#### "certificate verify failed"
**Cause**: Server was restarted or certificates were regenerated.

**Solution**: Generate a new operator configuration (see above).

#### Connection Timeouts
**Causes**:
- Server not running
- Firewall blocking port 31337
- Wrong server address in config

**Debug Steps**:
```bash
# Check if server is listening
netstat -tlnp | grep 31337

# Test connectivity
telnet localhost 31337

# Check firewall (Linux)
sudo iptables -L | grep 31337
```

### Certificate Validation

To inspect certificate details in your config:
```python
import json
from pathlib import Path

config_path = Path("~/.sliver-client/configs/wish.cfg").expanduser()
with open(config_path, 'r') as f:
    config = json.load(f)
    
print(f"Server: {config.get('lhost')}:{config.get('lport')}")
print(f"Operator: {config.get('operator')}")
print(f"Has CA cert: {'ca_certificate' in config}")
print(f"Has client cert: {'certificate' in config}")
print(f"Has private key: {'private_key' in config}")
```

## Security Best Practices

### For Production Use

1. **Unique Operators**: Generate separate configs for each user
   ```bash
   sliver-server operator --name alice --lhost server.example.com --save alice.cfg
   sliver-server operator --name bob --lhost server.example.com --save bob.cfg
   ```

2. **Network Security**: 
   - Use actual hostnames/IPs (not localhost) for remote access
   - Configure firewall rules to limit access
   - Consider VPN for additional security

3. **File Permissions**: Configs are automatically created with 600 permissions. Verify:
   ```bash
   chmod 600 ~/.sliver-client/configs/*.cfg
   ```

4. **Audit Logs**: Sliver logs all operator actions. Monitor:
   ```bash
   # Check Sliver logs
   sudo journalctl -u sliver-server
   ```

### For Development/Testing

1. **Mock Mode**: Use mock mode for development without a real server:
   ```toml
   [c2.sliver]
   enabled = true
   mode = "mock"
   ```

2. **Local Testing**: Use localhost configurations for isolated testing

3. **Cleanup**: Remove test configs when done:
   ```bash
   rm ~/.sliver-client/configs/test-*.cfg
   ```

## Next Steps

1. **Generate Implants**: Use Sliver to create implants for target systems
2. **Execute Commands**: Use wish's `/sliver shell` command
3. **Explore Features**: Try file operations, port forwarding, etc.

## Additional Resources

- [Sliver Documentation](https://github.com/BishopFox/sliver/wiki)
- [Sliver C2 Blog](https://bishopfox.com/blog/sliver-command-and-control)
- [wish C2 Package Docs](../packages/wish-c2/README.md)