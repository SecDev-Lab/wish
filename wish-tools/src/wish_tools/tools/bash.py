"""
Bash tool implementation for wish framework.

This tool provides a wrapper around bash command execution,
compatible with the existing wish-command-execution backend.
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

from wish_tools.framework.base import (
    BaseTool, ToolMetadata, ToolCapability, ToolContext, ToolResult, CommandInput
)


class BashTool(BaseTool):
    """Bash shell command execution tool."""
    
    def _build_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="bash",
            version="1.0.0",
            description="Fallback shell command execution when no specialized tool is available",
            author="Wish Framework Team",
            category="fallback",
            capabilities=[
                ToolCapability(
                    name="execute",
                    description="Execute any bash command (used when specialized tools are unavailable)",
                    parameters={
                        "command": "The bash command to execute",
                        "timeout": "Timeout in seconds (optional, default: 300)",
                        "category": "Command category hint (optional: network, file, process, system, web, text)"
                    },
                    examples=[
                        "# Network enumeration fallback",
                        "nc -zv 192.168.1.1 22-443",
                        "ping -c 4 8.8.8.8",
                        "# File operations fallback", 
                        "find /etc -name '*.conf' -type f",
                        "grep -r 'password' /var/log/",
                        "# Process management fallback",
                        "ps aux | grep nginx",
                        "netstat -tulpn | grep :80",
                        "# System information fallback",
                        "uname -a && cat /etc/os-release",
                        "df -h && free -h"
                    ]
                ),
                ToolCapability(
                    name="script",
                    description="Execute custom bash scripts for complex operations",
                    parameters={
                        "script": "The bash script content",
                        "args": "Script arguments (optional)"
                    },
                    examples=[
                        "#!/bin/bash\n# Custom enumeration script\nfor port in 22 80 443; do nc -zv $1 $port; done",
                        "#!/bin/bash\n# Log analysis script\ngrep 'ERROR' /var/log/*.log | tail -20"
                    ]
                ),
                ToolCapability(
                    name="tool_combination",
                    description="Combine multiple tools with pipes and logic when no single specialized tool exists",
                    parameters={
                        "command": "Complex command combining multiple tools",
                        "description": "Description of what the combined command does"
                    },
                    examples=[
                        "# Network discovery + service detection",
                        "nmap -sn 192.168.1.0/24 | grep 'Nmap scan report' | awk '{print $5}' | xargs -I {} nmap -sV -p 22,80,443 {}",
                        "# Log analysis with multiple filters",
                        "cat /var/log/auth.log | grep 'Failed password' | awk '{print $11}' | sort | uniq -c | sort -nr"
                    ]
                )
            ],
            requirements=["bash"],
            tags=["shell", "fallback", "general-purpose", "universal"]
        )
    
    async def validate_availability(self) -> tuple[bool, Optional[str]]:
        """Check if bash is available."""
        try:
            result = subprocess.run(
                ["bash", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, None
            else:
                return False, "Bash returned non-zero exit code"
        except FileNotFoundError:
            return False, "Bash not found in PATH"
        except subprocess.TimeoutExpired:
            return False, "Bash version check timed out"
        except Exception as e:
            return False, f"Error checking bash availability: {str(e)}"
    
    async def execute(
        self,
        command: CommandInput,
        context: ToolContext,
        **kwargs
    ) -> ToolResult:
        """Execute a bash command."""
        start_time = time.time()
        
        try:
            # Prepare environment
            env = dict(context.environment_variables)
            env.update(kwargs.get("env", {}))
            
            # Create working directory if it doesn't exist
            work_dir = Path(context.working_directory)
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Run bash command
            process = await asyncio.create_subprocess_shell(
                command.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.working_directory,
                env=env if env else None
            )
            
            # Set up timeout
            timeout = command.timeout_sec or context.timeout_override or 300
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    output="",
                    error="Command timed out",
                    exit_code=124,  # Standard timeout exit code
                    execution_time=timeout,
                    metadata={"timeout": True, "command": command.command}
                )
            
            # Decode output
            output = stdout.decode('utf-8', errors='replace') if stdout else ""
            error = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=process.returncode == 0,
                output=output,
                error=error if error else None,
                exit_code=process.returncode or 0,
                execution_time=execution_time,
                metadata={
                    "command": command.command,
                    "working_directory": context.working_directory,
                    "run_id": context.run_id
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                exit_code=-1,
                execution_time=time.time() - start_time,
                metadata={"command": command.command, "error_type": type(e).__name__}
            )
    
    def generate_command(
        self,
        capability: str,
        parameters: Dict[str, Any],
        context: Optional[ToolContext] = None
    ) -> CommandInput:
        """Generate a bash command for the specified capability."""
        if capability == "execute":
            return CommandInput(
                command=parameters["command"],
                timeout_sec=parameters.get("timeout", 300)
            )
            
        elif capability == "script":
            # Create a temporary script file and execute it
            script_content = parameters["script"]
            args = parameters.get("args", "")
            
            # For now, use a simple inline approach
            # In production, might want to write to a temp file
            escaped_script = script_content.replace("'", "'\"'\"'")
            command = f"bash -c '{escaped_script}'"
            if args:
                command += f" {args}"
            
            return CommandInput(
                command=command,
                timeout_sec=parameters.get("timeout", 300)
            )
            
        elif capability == "file_ops":
            operation = parameters["operation"]
            
            if operation == "read":
                command = f"cat '{parameters['source']}'"
            elif operation == "write":
                content = parameters["content"]
                target = parameters["target"]
                # Escape content for shell
                escaped_content = content.replace("'", "'\"'\"'")
                command = f"echo '{escaped_content}' > '{target}'"
            elif operation == "copy":
                command = f"cp '{parameters['source']}' '{parameters['target']}'"
            elif operation == "move":
                command = f"mv '{parameters['source']}' '{parameters['target']}'"
            else:
                raise ValueError(f"Unknown file operation: {operation}")
            
            return CommandInput(
                command=command,
                timeout_sec=parameters.get("timeout", 60)
            )
            
        else:
            raise ValueError(f"Unknown capability: {capability}")
    
    def validate_command(self, command: CommandInput) -> tuple[bool, Optional[str]]:
        """Validate bash command syntax and safety."""
        cmd = command.command.strip()
        
        # Basic safety checks
        dangerous_patterns = [
            "rm -rf /",
            ":(){ :|:& };:",  # Fork bomb
            "dd if=/dev/zero",
            "mkfs.",
            "fdisk",
            "parted"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in cmd.lower():
                return False, f"Command contains dangerous pattern: {pattern}"
        
        # Check for empty command
        if not cmd:
            return False, "Command cannot be empty"
        
        return True, None# Test change
