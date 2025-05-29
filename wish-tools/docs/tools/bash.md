# bash

Fallback shell command execution when no specialized tool is available

**Version:** 1.0.0
**Author:** Wish Framework Team
**Category:** fallback
**Tags:** shell, fallback, general-purpose, universal

## Requirements
- bash

## Capabilities

### execute
Execute any bash command (used when specialized tools are unavailable)

**Parameters:**
- `command`: The bash command to execute
- `timeout`: Timeout in seconds (optional, default: 300)
- `category`: Command category hint (optional: network, file, process, system, web, text)

**Examples:**
```bash
# Network enumeration fallback
```
```bash
nc -zv 192.168.1.1 22-443
```
```bash
ping -c 4 8.8.8.8
```
```bash
# File operations fallback
```
```bash
find /etc -name '*.conf' -type f
```
```bash
grep -r 'password' /var/log/
```
```bash
# Process management fallback
```
```bash
ps aux | grep nginx
```
```bash
netstat -tulpn | grep :80
```
```bash
# System information fallback
```
```bash
uname -a && cat /etc/os-release
```
```bash
df -h && free -h
```

### script
Execute custom bash scripts for complex operations

**Parameters:**
- `script`: The bash script content
- `args`: Script arguments (optional)

**Examples:**
```bash
#!/bin/bash
# Custom enumeration script
for port in 22 80 443; do nc -zv $1 $port; done
```
```bash
#!/bin/bash
# Log analysis script
grep 'ERROR' /var/log/*.log | tail -20
```

### tool_combination
Combine multiple tools with pipes and logic when no single specialized tool exists

**Parameters:**
- `command`: Complex command combining multiple tools
- `description`: Description of what the combined command does

**Examples:**
```bash
# Network discovery + service detection
```
```bash
nmap -sn 192.168.1.0/24 | grep 'Nmap scan report' | awk '{print $5}' | xargs -I {} nmap -sV -p 22,80,443 {}
```
```bash
# Log analysis with multiple filters
```
```bash
cat /var/log/auth.log | grep 'Failed password' | awk '{print $11}' | sort | uniq -c | sort -nr
```