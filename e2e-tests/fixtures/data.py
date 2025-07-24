"""Test data and constants for E2E testing."""

from datetime import datetime

from wish_ai.planning.models import Plan, PlanStep
from wish_models import Finding, Host, Service

# Mock tool outputs
MOCK_NMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun>
    <host>
        <address addr="10.10.10.3" addrtype="ipv4"/>
        <hostnames>
            <hostname name="lame.htb" type="PTR"/>
        </hostnames>
        <ports>
            <port protocol="tcp" portid="21">
                <state state="open" reason="syn-ack"/>
                <service name="ftp" product="vsftpd" version="2.3.4"/>
            </port>
            <port protocol="tcp" portid="22">
                <state state="open" reason="syn-ack"/>
                <service name="ssh" product="OpenSSH" version="4.7p1"/>
            </port>
            <port protocol="tcp" portid="139">
                <state state="open" reason="syn-ack"/>
                <service name="netbios-ssn" product="Samba smbd" version="3.X - 4.X"/>
            </port>
            <port protocol="tcp" portid="445">
                <state state="open" reason="syn-ack"/>
                <service name="netbios-ssn" product="Samba smbd" version="3.0.20-Debian"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

MOCK_NMAP_OUTPUT = """Starting Nmap 7.93 ( https://nmap.org )
Nmap scan report for 10.10.10.3
Host is up (0.050s latency).

PORT    STATE SERVICE     VERSION
21/tcp  open  ftp         vsftpd 2.3.4
22/tcp  open  ssh         OpenSSH 4.7p1 Debian 8ubuntu1 (protocol 2.0)
139/tcp open  netbios-ssn Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
445/tcp open  netbios-ssn Samba smbd 3.0.20-Debian (workgroup: WORKGROUP)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 12.34 seconds"""

MOCK_NIKTO_OUTPUT = """- Nikto v2.1.6
+ Target IP:          10.10.10.3
+ Target Hostname:    lame.htb
+ Target Port:        80
+ Start Time:         2024-01-01 12:00:00
+ Server: Apache/2.2.3 (Ubuntu) DAV/2
+ Retrieved x-powered-by header: PHP/5.2.4-2ubuntu5.10
+ The anti-clickjacking X-Frame-Options header is not present.
+ The X-XSS-Protection header is not defined.
+ Apache/2.2.3 appears to be outdated (current is at least Apache/2.4.37).
+ OSVDB-877: HTTP TRACE method is active
+ OSVDB-3268: /css/: Directory indexing found.
+ OSVDB-3092: /LICENSE.txt: License file found."""

MOCK_GOBUSTER_OUTPUT = """/index.html           (Status: 200) [Size: 891]
/images               (Status: 301) [Size: 314]
/css                  (Status: 301) [Size: 311]
/js                   (Status: 301) [Size: 310]
/admin                (Status: 401) [Size: 461]
/backup               (Status: 301) [Size: 314]"""

MOCK_EXPLOIT_OUTPUT = """[*] Attempting to exploit Samba username map script...
[+] Connecting to target on port 445
[+] Sending malicious username
[+] Command injection successful!
[+] Shell obtained!

# whoami
root
# id
uid=0(root) gid=0(root) groups=0(root)"""


def sample_host() -> Host:
    """Create a sample host for testing."""
    host = Host(ip_address="10.10.10.3", discovered_by="nmap")
    host.add_hostname("lame.htb")

    # Add services
    host.services = [
        Service(
            host_id=host.id,
            port=21,
            protocol="tcp",
            service_name="ftp",
            state="open",
            product="vsftpd",
            version="2.3.4",
            discovered_by="nmap"
        ),
        Service(
            host_id=host.id,
            port=22,
            protocol="tcp",
            service_name="ssh",
            state="open",
            product="OpenSSH",
            version="4.7p1",
            discovered_by="nmap"
        ),
        Service(
            host_id=host.id,
            port=445,
            protocol="tcp",
            service_name="netbios-ssn",
            state="open",
            product="Samba smbd",
            version="3.0.20-Debian",
            discovered_by="nmap"
        ),
    ]

    return host


def sample_finding() -> Finding:
    """Create a sample finding for testing."""
    host = sample_host()
    samba_service = next(s for s in host.services if s.port == 445)

    return Finding(
        id="finding-cve-2007-2447",
        title="Samba Username Map Script Command Execution",
        description=(
            "The Samba server is vulnerable to remote command execution "
            "via username map script (CVE-2007-2447)"
        ),
        category="vulnerability",
        severity="critical",
        target_type="service",
        host_id=host.id,
        service_id=samba_service.id,
        vulnerability_id="CVE-2007-2447",
        discovered_by="manual",
        discovery_date=datetime.now(),
        evidence={
            "version": "3.0.20-Debian",
            "vulnerable_versions": "3.0.0 - 3.0.25rc3",
            "exploit_available": True
        }
    )


def sample_plan(description: str = "Test plan") -> Plan:
    """Create a sample plan for testing."""
    return Plan(
        description=description,
        steps=[
            PlanStep(
                tool_name="nmap",
                command="nmap -sV -sC 10.10.10.3",
                purpose="Scan for open ports and services",
                expected_result="List of open ports with service details"
            ),
            PlanStep(
                tool_name="enum4linux",
                command="enum4linux -a 10.10.10.3",
                purpose="Enumerate SMB shares and users",
                expected_result="SMB configuration details"
            )
        ],
        rationale="Comprehensive scanning and enumeration strategy"
    )


# Test scenarios data
HTB_LAME_SCENARIO = {
    "target": "10.10.10.3",
    "hostname": "lame.htb",
    "vulnerability": "CVE-2007-2447",
    "expected_services": [
        {"port": 21, "service": "ftp", "product": "vsftpd"},
        {"port": 22, "service": "ssh", "product": "OpenSSH"},
        {"port": 139, "service": "netbios-ssn", "product": "Samba"},
        {"port": 445, "service": "netbios-ssn", "product": "Samba"},
    ],
    "exploit_path": "Samba username map script command execution",
    "expected_privs": "root"
}

# Error scenarios
ERROR_SCENARIOS = [
    {
        "name": "Invalid Target",
        "command": "scan invalid.target.local",
        "expected_error": "resolution"
    },
    {
        "name": "Dangerous Command",
        "command": "delete all files in /etc",
        "expected_action": "reject"
    },
    {
        "name": "Tool Not Found",
        "command": "run nonexistent-tool",
        "expected_error": "tool not found"
    },
    {
        "name": "Network Timeout",
        "command": "scan 10.255.255.255",
        "expected_error": "timeout"
    }
]

# Dangerous command patterns for safety testing
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"dd\s+if=/dev/zero",
    r":\(\)\{\s*:\|:&\s*\};:",  # Fork bomb
    r"chmod\s+777\s+/",
    r"mkfs\.",
    r"format\s+[cC]:",
]
