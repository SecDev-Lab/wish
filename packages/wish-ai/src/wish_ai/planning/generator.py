"""
AI-powered plan generation for penetration testing.

This module implements the PlanGenerator class that uses LLMs to create
structured penetration testing plans based on user input and engagement state.
"""

import json
import logging
import re
from typing import Any

from wish_models import EngagementState

from ..gateway.base import LLMGateway
from .models import Plan, PlanStep, RiskLevel

logger = logging.getLogger(__name__)


class PlanGenerator:
    """AI-powered generator for penetration testing plans.

    This class uses an LLM gateway to generate structured plans based on
    user input and current engagement state.
    """

    def __init__(self, llm_gateway: LLMGateway):
        """Initialize the plan generator.

        Args:
            llm_gateway: LLM gateway instance for AI communication
        """
        self.llm_gateway = llm_gateway
        logger.info(f"Initialized PlanGenerator with {llm_gateway.__class__.__name__}")

    async def generate_plan(
        self, user_input: str, engagement_state: EngagementState, context: dict[str, Any] | None = None
    ) -> Plan:
        """Generate a penetration testing plan based on user input and state.

        Args:
            user_input: Natural language description of what the user wants to do
            engagement_state: Current penetration testing engagement state
            context: Additional context information

        Returns:
            Generated Plan object

        Raises:
            PlanGenerationError: If plan generation fails
        """
        try:
            logger.info(f"Generating plan for input: {user_input[:100]}...")
            logger.debug(f"Full user input: {user_input}")

            # Build the prompt for plan generation
            logger.debug("Building plan prompt...")
            prompt = self._build_plan_prompt(user_input, engagement_state, context or {})
            logger.debug(f"Prompt length: {len(prompt)} characters")

            # Generate response from LLM
            logger.debug("Calling LLM gateway to generate plan...")
            response = await self.llm_gateway.generate_plan(
                prompt=prompt, context={"mode": engagement_state.get_current_mode(), "user_input": user_input}
            )
            logger.debug(f"Received LLM response: {len(response)} characters")

            # Parse the response into a Plan object
            logger.debug("Parsing plan response...")
            plan = self._parse_plan_response(response, engagement_state.get_current_mode())

            logger.info(f"Generated plan with {plan.total_steps} steps")
            return plan

        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            raise PlanGenerationError(f"Failed to generate plan: {str(e)}") from e

    def _build_plan_prompt(self, user_input: str, engagement_state: EngagementState, context: dict[str, Any]) -> str:
        """Build the prompt for plan generation.

        Args:
            user_input: User's natural language input
            engagement_state: Current engagement state
            context: Additional context

        Returns:
            Formatted prompt string
        """
        # Get current state summary
        active_hosts = engagement_state.get_active_hosts()
        targets = list(engagement_state.targets.values())
        findings = list(engagement_state.findings.values())

        # Build context sections
        targets_context = self._format_targets_context(targets)
        hosts_context = self._format_hosts_context(active_hosts)
        findings_context = self._format_findings_context(findings)

        # Tools context disabled

        prompt = f"""You are WISH, an AI-powered penetration testing assistant. \
Generate a structured plan based on the user's request.

## Current Context

**Mode**: {engagement_state.get_current_mode()}
**Current Phase**: {context.get("phase", "reconnaissance") if context else "reconnaissance"}

{targets_context}

{hosts_context}

{findings_context}


## User Request

{user_input}

## Instructions

Generate a penetration testing plan as a JSON object with the following structure:

```json
{{
    "description": "Brief description of what this plan accomplishes",
    "rationale": "Explanation of why this approach was chosen",
    "estimated_duration": 30,
    "steps": [
        {{
            "tool_name": "nmap",
            "command": "nmap -sV -sC -O -T4 --max-retries 2 target",
            "purpose": "Detailed service and OS detection",
            "expected_result": "Service versions and OS information",
            "risk_level": "low",
            "timeout": 120,
            "requires_confirmation": false
        }}
    ]
}}
```

## Available Tools

You can use ANY standard penetration testing tool. Common tools include:
- **nmap**: Network scanner for port discovery and service detection
- **nikto**: Web server scanner for vulnerabilities
- **gobuster**: Directory/file brute-forcer for web content discovery
- **enum4linux**: SMB/NetBIOS enumeration tool
- **smbclient**: SMB client for accessing shares
- **rpcclient**: RPC client for Windows systems
- **nbtscan**: NetBIOS scanner
- **onesixtyone**: SNMP scanner
- **snmpwalk**: SNMP enumeration tool
- **hydra**: Network login cracker
- **medusa**: Parallel network login auditor
- **wpscan**: WordPress vulnerability scanner
- **sqlmap**: SQL injection detection and exploitation
- **dirb**: Web content scanner
- **dirbuster**: Web application brute forcer
- **wfuzz**: Web application fuzzer
- **ffuf**: Fast web fuzzer
- **masscan**: Fast port scanner
- **unicornscan**: Advanced port scanner
- **amap**: Application protocol detection
- **sslscan**: SSL/TLS scanner
- **sslyze**: SSL/TLS scanner
- **testssl.sh**: SSL/TLS tester
- **msfconsole**: Metasploit Framework console
- And many more... use appropriate tools for the task

## Guidelines

1. **Tool Requirement**: Only generate steps if the request requires executing tools or commands
2. **Knowledge Questions**: For questions about vulnerabilities, exploits, or general knowledge:
   - Return an EMPTY steps array (`"steps": []`)
   - Put brief answer in `description` field
   - Put DETAILED vulnerability information in `rationale` field
   - For Samba 3.0.20, ALWAYS mention CVE-2007-2447 (username map script vulnerability)
3. **Be Specific**: If the user request is vague, make reasonable assumptions and generate practical steps
4. **Risk Assessment**: Set appropriate risk levels (low/medium/high/critical)
5. **Tool Selection**: Choose appropriate tools based on the current mode and discovered services
6. **Scope Compliance**: Only target hosts/services within the defined scope
7. **Logical Progression**: Ensure steps build upon each other logically
8. **Safety First**: Mark high-risk operations as requiring confirmation
9. **Scan Optimization**:
   - For nmap scans, always use timing template flags (-T3 or -T4)
   - For comprehensive scans (-sV -sC -O), set timeout to 120 seconds
   - For quick scans (port only), set timeout to 60 seconds
   - Use --max-retries 2 to limit scan time on unresponsive ports
   - Example optimized nmap: `nmap -sV -sC -O -T4 --max-retries 2 target`

## Important Rules

- If the user asks to "scan" a target, generate specific nmap or other scanning commands
- If the user request lacks specific details, use common penetration testing workflows
- For action-oriented requests (scan, enumerate, exploit), generate concrete steps
- For knowledge-based questions (what vulnerabilities, how does X work), return EMPTY steps array
- Each step MUST have all required fields: tool_name, command, purpose, expected_result
- **Use real penetration testing tools that exist and can be executed**
- **NEVER create fictional tools like "manual_research" or "knowledge_base"**
- **When available, use the example commands from the suggested tools section**

Generate the plan now:"""

        return prompt

    def _format_targets_context(self, targets: list) -> str:
        """Format targets information for the prompt."""
        if not targets:
            return "**Targets**: None defined"

        in_scope = [t for t in targets if t.in_scope]
        if not in_scope:
            return "**Targets**: No targets in scope"

        target_list = []
        for target in in_scope[:5]:  # Limit to 5 targets
            target_list.append(f"- {target.scope} ({target.scope_type})")

        result = "**Targets**:\n" + "\n".join(target_list)
        if len(in_scope) > 5:
            result += f"\n- ... and {len(in_scope) - 5} more targets"

        return result

    def _format_hosts_context(self, hosts: list) -> str:
        """Format discovered hosts information for the prompt."""
        if not hosts:
            return "**Discovered Hosts**: None"

        host_list = []
        for host in hosts[:5]:  # Limit to 5 hosts
            open_ports = len([s for s in host.services if s.state == "open"])
            host_list.append(f"- {host.ip_address}: {open_ports} open ports")

        result = "**Discovered Hosts**:\n" + "\n".join(host_list)
        if len(hosts) > 5:
            result += f"\n- ... and {len(hosts) - 5} more hosts"

        return result

    def _format_findings_context(self, findings: list) -> str:
        """Format current findings for the prompt."""
        if not findings:
            return "**Findings**: None yet"

        # Group by severity
        severity_counts: dict[str, int] = {}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

        severity_list = []
        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in severity_counts:
                severity_list.append(f"- {severity.capitalize()}: {severity_counts[severity]}")

        result = "**Findings**:\n" + "\n".join(severity_list)

        # Add high-priority findings details
        high_priority = [f for f in findings if f.severity in ["critical", "high"]]
        if high_priority:
            result += "\n\n**High Priority Issues**:\n"
            for finding in high_priority[:3]:  # Limit to 3
                result += f"- {finding.title} ({finding.severity})\n"

        return result

    def _parse_plan_response(self, response: str, mode: str) -> Plan:
        """Parse LLM response into a structured Plan object.

        Args:
            response: Raw response from the LLM
            mode: Current engagement mode

        Returns:
            Parsed Plan object

        Raises:
            PlanGenerationError: If parsing fails
        """
        try:
            # Extract JSON from response
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if not json_match:
                # Try to find JSON without code blocks
                json_match = re.search(r"(\{.*?\})", response, re.DOTALL)

            if not json_match:
                raise PlanGenerationError("No valid JSON found in LLM response")

            json_str = json_match.group(1)
            plan_data = json.loads(json_str)

            # Validate required fields
            required_fields = ["description", "rationale", "steps"]
            for field in required_fields:
                if field not in plan_data:
                    raise PlanGenerationError(f"Missing required field: {field}")

            # Parse steps
            steps = []
            for i, step_data in enumerate(plan_data["steps"]):
                try:
                    step = self._parse_plan_step(step_data)
                    steps.append(step)
                except Exception as e:
                    logger.warning(f"Failed to parse step {i}: {e}")
                    continue

            # Empty steps is valid for knowledge-based responses
            if (
                not steps
                and "steps" in plan_data
                and isinstance(plan_data["steps"], list)
                and len(plan_data["steps"]) == 0
            ):
                # This is intentionally empty - knowledge-based response
                logger.info("Knowledge-based response with no steps")
            elif not steps:
                # Steps failed to parse
                logger.error(f"No valid steps found in plan. LLM response: {plan_data}")
                raise PlanGenerationError(
                    "Failed to parse plan steps from LLM response. "
                    "This might be due to an unexpected response format. "
                    "Please try rephrasing your request or be more specific."
                )

            # Create Plan object
            plan = Plan(
                description=plan_data["description"],
                rationale=plan_data["rationale"],
                steps=steps,
                estimated_duration=plan_data.get("estimated_duration"),
                mode=mode,
                created_by="AI",
            )

            return plan

        except json.JSONDecodeError as e:
            raise PlanGenerationError(f"Invalid JSON in LLM response: {e}") from e
        except Exception as e:
            raise PlanGenerationError(f"Failed to parse plan response: {e}") from e

    def _parse_plan_step(self, step_data: dict) -> PlanStep:
        """Parse a single step from the plan data.

        Args:
            step_data: Dictionary containing step information

        Returns:
            PlanStep object

        Raises:
            ValueError: If step data is invalid
        """
        required_fields = ["tool_name", "command", "purpose", "expected_result"]
        for field in required_fields:
            if field not in step_data:
                raise ValueError(f"Missing required step field: {field}")

        # Parse risk level
        risk_level_str = step_data.get("risk_level", "low").lower()
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel.LOW
            logger.warning(f"Invalid risk level '{risk_level_str}', defaulting to low")

        # Handle Metasploit command format
        tool_name = step_data["tool_name"]
        command = step_data["command"]

        # Auto-fix legacy Metasploit commands
        if command.startswith("use exploit/") or command.startswith("use auxiliary/"):
            # Fix tool_name
            if tool_name not in ["msfconsole", "metasploit"]:
                logger.warning(f"Auto-correcting tool_name from '{tool_name}' to 'msfconsole' for Metasploit command")
                tool_name = "msfconsole"

            # Fix command format to be executable
            if not command.startswith("msfconsole"):
                logger.warning(f"Auto-converting Metasploit command to executable format: {command}")
                command = f'msfconsole -q -x "{command}; exit"'

        return PlanStep(
            tool_name=tool_name,
            command=command,
            purpose=step_data["purpose"],
            expected_result=step_data["expected_result"],
            risk_level=risk_level,
            timeout=step_data.get("timeout"),
            requires_confirmation=step_data.get("requires_confirmation", False),
        )


class PlanGenerationError(Exception):
    """Raised when plan generation fails."""

    pass
