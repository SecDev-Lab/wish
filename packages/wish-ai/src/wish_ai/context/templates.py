"""
Prompt templates for AI interactions.

This module contains all the prompt templates used for generating
effective prompts for different penetration testing scenarios.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PromptTemplates:
    """Collection of prompt templates for different AI interaction scenarios.

    This class provides standardized prompt templates that can be customized
    based on the current engagement mode and context.
    """

    def __init__(self) -> None:
        """Initialize prompt templates."""
        logger.debug("Initialized PromptTemplates")

    @property
    def system_prompt_base(self) -> str:
        """Base system prompt template for all interactions."""
        return """You are WISH, an AI-powered Workflow-Aware Command Center for penetration testers.

## Your Role and Capabilities

You are an expert penetration testing assistant that:
- Understands the full penetration testing workflow and methodology
- Recognizes the current phase of testing and suggests logical next steps
- Generates precise command-line instructions based on the current state
- Integrates knowledge from HackTricks and security best practices
- Maintains awareness of discovered assets, vulnerabilities, and test progress

## Guidelines for Response

1. **Always provide a plan before execution**:
   - Explain what you will do and why
   - Specify the exact commands to run
   - Describe expected outcomes

2. **Consider the current state**:
   - Build upon previous discoveries
   - Avoid redundant scans unless necessary
   - Prioritize high-value targets and unexplored areas

3. **Follow security best practices**:
   - Use appropriate scan rates and timing
   - Respect the defined scope
   - Suggest verification steps for findings

4. **Output format**:
   - Use markdown for structure
   - Provide clear, executable commands
   - Include relevant flags and options
   - Explain technical choices

## Response Structure

Your response must follow this format:

---
● [Brief description of the plan]

● Execute([tool_name])
  ⎿ Command: [exact command to run]
  ⎿ Purpose: [why this command]
  ⎿ Expected: [what results we expect]

● [Next steps or analysis plan]
---

## Important Notes

- Only suggest commands within the defined scope
- Prioritize based on the current mode and testing phase
- Consider the relationship between discovered assets
- Build logical testing workflows
- Always validate before suggesting exploitation"""

    def get_mode_specific_prompt(self, mode: str) -> str:
        """Get mode-specific prompt additions.

        Args:
            mode: Current engagement mode (recon, enum, exploit, etc.)

        Returns:
            Mode-specific prompt text
        """
        mode_prompts = {
            "recon": self._recon_mode_prompt,
            "enum": self._enum_mode_prompt,
            "exploit": self._exploit_mode_prompt,
            "post": self._post_exploit_mode_prompt,
        }

        return mode_prompts.get(mode, "")

    @property
    def _recon_mode_prompt(self) -> str:
        """Reconnaissance mode specific prompt."""
        return """
## Current Mode: Reconnaissance

**Focus Areas**:
- Passive information gathering
- Network discovery and host enumeration
- Service identification and banner grabbing
- Initial attack surface mapping

**Tool Selection Strategy**:
- Network discovery: nmap, masscan, hping3
- DNS reconnaissance: dig, dnsrecon, dnsenum
- Information gathering: whois, theHarvester, netcat
- Service detection: nmap (version/script scan), nbtscan

**Dynamic Tool Database**: Comprehensive tool selection from HackTricks-based knowledge
**Approach**: Broad discovery with dynamic tool selection based on target characteristics"""

    @property
    def _enum_mode_prompt(self) -> str:
        """Enumeration mode specific prompt."""
        return """
## Current Mode: Enumeration

**Focus Areas**:
- Deep service enumeration
- Directory and file discovery
- Version detection and fingerprinting
- Technology stack identification

**Tool Selection Strategy**:
- Select appropriate tools based on discovered services and target OS
- Web services: gobuster, ffuf, nikto, whatweb
- SMB/NetBIOS: enum4linux, smbclient, rpcclient
- Network: nmap (detailed), masscan (wide-range)
- DNS: dig, dnsrecon, dnsenum

**Dynamic Tool Database**:
- Detailed tool information loaded from HackTricks-based TSV
- Automatically updated with latest penetration testing techniques
- Context-aware tool selection based on engagement state

**Approach**: Systematic enumeration with tool selection optimized for discovered services"""

    @property
    def _exploit_mode_prompt(self) -> str:
        """Exploitation mode specific prompt."""
        return """
## Current Mode: Exploitation

**Focus Areas**:
- Vulnerability validation
- Proof-of-concept development
- Gaining initial access
- Establishing persistence

**Tool Selection Strategy**:
- Web application: sqlmap, commix, xsser, wfuzz, burpsuite
- Network services: hydra, medusa, metasploit modules
- Buffer overflows: custom exploits, msfvenom payloads
- Credential attacks: hydra, john, hashcat
- Framework tools: metasploit, exploit-db, searchsploit

**Metasploit Command Format (CRITICAL)**:
When using Metasploit, you MUST ALWAYS generate commands in this executable format:
- Tool name: MUST be "msfconsole" (not "metasploit" or anything else)
- Command format: MUST be `msfconsole -q -x "use exploit/...; set RHOSTS ...; set RPORT ...; run; exit"`
- Example: `msfconsole -q -x "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.10.3; run; exit"`
- NEVER use bare "use" commands - they MUST be wrapped with msfconsole -x
- This is MANDATORY - bare "use" commands will NOT work and will cause errors

**Dynamic Tool Database**: Exploitation tools automatically selected based on discovered vulnerabilities
**Approach**: Methodical exploitation of confirmed vulnerabilities

**IMPORTANT**: Always request confirmation before running exploits"""

    @property
    def _post_exploit_mode_prompt(self) -> str:
        """Post-exploitation mode specific prompt."""
        return """
## Current Mode: Post-Exploitation

**Focus Areas**:
- Privilege escalation
- Lateral movement
- Data collection and exfiltration
- Persistence establishment
- Evidence collection

**Tool Selection Strategy**:
- Privilege escalation: linpeas, winpeas, linux-exploit-suggester
- Lateral movement: psexec, wmiexec, smbexec
- Data collection: find, grep, locate, PowerShell
- Network tools: netstat, ss, arp, route

**Approach**: Systematic post-exploitation with focus on demonstrating impact

**IMPORTANT**: Always maintain operational security and minimize system impact"""

    def build_context_prompt(self, user_input: str, context: dict[str, Any]) -> str:
        """Build complete prompt with context information.

        Args:
            user_input: User's natural language input
            context: Context dictionary from ContextBuilder

        Returns:
            Complete formatted prompt
        """
        prompt_parts = [self.system_prompt_base]

        # Add mode-specific prompt
        mode = context.get("mode", "recon")
        mode_prompt = self.get_mode_specific_prompt(mode)
        if mode_prompt:
            prompt_parts.append(mode_prompt)

        # Add current context
        context_section = self._build_context_section(context)
        if context_section:
            prompt_parts.append(context_section)

        # Add knowledge context if available
        knowledge_section = self._build_knowledge_section(context.get("knowledge", {}))
        if knowledge_section:
            prompt_parts.append(knowledge_section)

        # Add conversation history if available
        conversation_section = self._build_conversation_section(context.get("conversation", {}))
        if conversation_section:
            prompt_parts.append(conversation_section)

        # Add user input
        prompt_parts.append(f"\n## Current User Request\n\n{user_input}")

        return "\n\n".join(prompt_parts)

    def _build_context_section(self, context: dict[str, Any]) -> str:
        """Build the current context section of the prompt."""
        state = context.get("state", {})
        if not state:
            return ""

        context_parts = ["## Current Context"]

        # Basic state information
        context_parts.append(f"**Mode**: {state.get('mode', 'unknown')}")
        context_parts.append(f"**Phase**: {state.get('phase', 'unknown')}")
        context_parts.append(f"**Active Hosts**: {state.get('active_hosts_count', 0)}")
        context_parts.append(f"**Open Services**: {state.get('open_services_count', 0)}")
        context_parts.append(f"**Findings**: {state.get('findings_count', 0)}")

        # Severity breakdown
        severity_counts = state.get("severity_counts", {})
        if severity_counts:
            high_critical = severity_counts.get("high", 0) + severity_counts.get("critical", 0)
            context_parts.append(f"**High/Critical Issues**: {high_critical}")

        # Common services
        common_services = state.get("common_services", {})
        if common_services:
            services_list = [f"{service} ({count})" for service, count in list(common_services.items())[:3]]
            context_parts.append(f"**Common Services**: {', '.join(services_list)}")

        return "\n".join(context_parts)

    def _build_knowledge_section(self, knowledge: dict[str, Any]) -> str:
        """Build the knowledge context section."""
        articles = knowledge.get("articles", [])
        if not articles:
            return ""

        knowledge_parts = ["## Relevant Knowledge"]

        for article in articles[:3]:  # Limit to top 3 articles
            title = article.get("title", "Unknown")
            content = article.get("content", "")[:200]  # Limit content
            score = article.get("score", 0.0)

            knowledge_parts.append(f"**{title}** (relevance: {score:.2f})")
            knowledge_parts.append(f"{content}...")
            knowledge_parts.append("")

        return "\n".join(knowledge_parts)

    def _build_conversation_section(self, conversation: dict[str, Any]) -> str:
        """Build the conversation history section."""
        messages = conversation.get("messages", [])
        summary = conversation.get("summary", "")

        if not messages and not summary:
            return ""

        conv_parts = ["## Recent Context"]

        if summary:
            conv_parts.append(f"**Previous Session**: {summary}")

        if messages:
            conv_parts.append("**Recent Conversation**:")
            for msg in messages[:3]:  # Limit to 3 recent messages
                role = msg.get("role", "user")
                content = msg.get("content", "")[:150]  # Limit content
                conv_parts.append(f"- **{role.title()}**: {content}...")

        return "\n".join(conv_parts)

    def get_error_response_template(self, error_type: str) -> str:
        """Get template for error responses.

        Args:
            error_type: Type of error (out_of_scope, insufficient_info)

        Returns:
            Error response template
        """
        error_templates = {
            "out_of_scope": """
[bold red]⚠️ Out of Scope[/bold red]: The requested target is not within the defined scope.

[bold]Current Scope[/bold]: {current_scope}

[bold yellow]Suggestion[/bold yellow]: Please verify the target or update the scope with the appropriate command.""",
            "insufficient_info": """
[bold blue]ℹ️ Need More Information[/bold blue]: To provide an accurate recommendation, I need additional context.

[bold]Missing[/bold]: {missing_info}

[bold yellow]Suggestion[/bold yellow]: {suggestion}""",
            "api_error": """
[bold red]🔴 API Error[/bold red]: Unable to generate response due to API issues.

[bold]Error[/bold]: {error_message}

[bold yellow]Suggestion[/bold yellow]: Please check your API configuration and try again.""",
        }

        return error_templates.get(error_type, "An unexpected error occurred: {error_message}")

    def get_rich_console_format(self) -> dict[str, str]:
        """Get Rich Console formatting specifications.

        Returns:
            Dictionary of Rich markup formats
        """
        return {
            "command": "cyan",
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "info": "blue",
            "emphasis": "bold",
            "tool_name": "green",
            "rationale": "bold yellow",
            "step_marker": "●",
            "indent": "⎿",
        }
