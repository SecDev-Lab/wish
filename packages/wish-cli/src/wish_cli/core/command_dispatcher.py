"""Command dispatcher for routing user inputs."""

import asyncio
import logging
import os
from typing import Any

from wish_ai.conversation.manager import ConversationManager
from wish_ai.planning.generator import PlanGenerator
from wish_ai.planning.models import Plan, PlanStep
from wish_core.session import SessionManager
from wish_core.state.manager import StateManager
from wish_knowledge import Retriever
from wish_models.session import SessionMetadata
from wish_tools.execution.executor import ToolExecutor
from wish_tools.parsers.nmap import NmapParser
from wish_tools.parsers.smb import Enum4linuxParser, SmbclientParser

from wish_cli.commands.slash_commands import SlashCommandHandler
from wish_cli.core.exploit_engine import ExploitEngine
from wish_cli.core.job_manager import JobInfo, JobStatus
from wish_cli.core.vulnerability_detector import VulnerabilityDetector
from wish_cli.ui.ui_manager import WishUIManager

logger = logging.getLogger(__name__)

# List of known interactive commands
INTERACTIVE_COMMANDS = {
    "ftp": "FTP client",
    "telnet": "Telnet client",
    "ssh": "SSH client",
    "sftp": "SFTP client",
    "msfconsole": "Metasploit console",
    "nc": "Netcat",
    "ncat": "Nmap netcat",
    "socat": "Socket cat",
    "mysql": "MySQL client",
    "psql": "PostgreSQL client",
    "redis-cli": "Redis client",
    "mongo": "MongoDB client",
    "sqlite3": "SQLite client",
    "python": "Python REPL",
    "python3": "Python3 REPL",
    "ipython": "IPython REPL",
    "irb": "Ruby REPL",
    "node": "Node.js REPL",
    "ghci": "Haskell REPL",
    "erl": "Erlang shell",
    "iex": "Elixir shell",
    # SMB/Windows enumeration tools
    "rpcclient": "RPC client for SMB/CIFS servers",
    "smbclient": "SMB/CIFS client",
    "wbinfo": "Winbind information tool",
    # Additional penetration testing tools
    "sqlplus": "Oracle SQL*Plus client",
    "impacket-psexec": "Impacket PSExec",
    "impacket-wmiexec": "Impacket WMI Exec",
    "impacket-dcomexec": "Impacket DCOM Exec",
    "evil-winrm": "Evil WinRM shell",
    "winexe": "Windows command execution",
}


def is_interactive_command(command: str) -> bool:
    """Check if a command is interactive with advanced argument analysis."""
    if not command:
        return False

    # Parse command into parts
    parts = command.split()
    if not parts:
        return False

    # Extract the base command (first word)
    base_cmd = os.path.basename(parts[0])

    # Check if command is in the basic interactive list, but allow override for special cases
    basic_interactive = base_cmd in INTERACTIVE_COMMANDS

    # Advanced argument-based detection for special cases
    advanced_result = _is_interactive_by_arguments(base_cmd, parts[1:])

    # If advanced detection provides a specific result, use it; otherwise use basic detection
    if advanced_result is not None:
        return advanced_result
    return basic_interactive


def _is_interactive_by_arguments(base_cmd: str, args: list[str]) -> bool | None:
    """Determine if a command is interactive based on its arguments."""
    # Handle smbclient special cases
    if base_cmd == "smbclient":
        # smbclient -L is non-interactive (list shares)
        # smbclient //server/share is interactive
        if "-L" in args:
            return False
        # If connecting to a specific share without -c option, it's interactive
        if any(arg.startswith("//") for arg in args) and "-c" not in args:
            return True
        return False

    # Handle enum4linux - typically non-interactive enumeration tool
    if base_cmd == "enum4linux":
        return False

    # Handle nmap - generally non-interactive unless in specific modes
    if base_cmd == "nmap":
        # Interactive modes like --script-trace or certain NSE scripts
        interactive_flags = ["--script-trace", "--packet-trace"]
        return any(flag in args for flag in interactive_flags)

    # Handle crackmapexec - typically non-interactive
    if base_cmd in ["crackmapexec", "cme"]:
        return False

    # Handle impacket tools that might spawn shells
    if base_cmd.startswith("impacket-") and base_cmd.endswith(("exec", "shell")):
        return True

    # Handle common one-liner vs interactive patterns
    if base_cmd in ["python", "python3", "perl", "ruby"]:
        # If -c flag is present, it's likely a one-liner (non-interactive)
        if "-c" in args:
            return False
        # If a script file is specified, it's non-interactive
        if any(arg.endswith((".py", ".pl", ".rb")) for arg in args):
            return False
        # Otherwise, assume interactive REPL
        return True

    # Return None to indicate no specific override (use default behavior)
    return None


def get_command_description(command: str) -> str:
    """Get description for an interactive command."""
    base_cmd = os.path.basename(command.split()[0] if command else "")
    return INTERACTIVE_COMMANDS.get(base_cmd, "Interactive command")


class CommandDispatcher:
    """Command routing and dispatch."""

    def __init__(
        self,
        ui_manager: WishUIManager,
        state_manager: StateManager,
        session_manager: SessionManager,
        conversation_manager: ConversationManager,
        plan_generator: PlanGenerator,
        tool_executor: ToolExecutor,
        c2_connector: Any | None = None,
        retriever: Retriever | None = None,
    ):
        self.ui_manager = ui_manager
        self.state_manager = state_manager
        self.session_manager = session_manager
        self.conversation_manager = conversation_manager
        self.plan_generator = plan_generator
        self.tool_executor = tool_executor
        self.c2_connector = c2_connector
        self.retriever = retriever

        # Slash command handler
        self.slash_handler = SlashCommandHandler(
            ui_manager=ui_manager,
            state_manager=state_manager,
            session_manager=session_manager,
            tool_executor=tool_executor,
            c2_connector=c2_connector,
        )
        # Set command dispatcher reference
        self.slash_handler.command_dispatcher = self

        # Session information
        self.current_session: SessionMetadata | None = None

        # Interactive shell state
        self.current_shell: Any = None

        # Tool parsers
        self.nmap_parser = NmapParser()
        self.smbclient_parser = SmbclientParser()
        self.enum4linux_parser = Enum4linuxParser()

        # Vulnerability detector
        self.vulnerability_detector = VulnerabilityDetector()

        # Exploit engine
        self.exploit_engine = ExploitEngine(tool_executor, demo_mode=False)

        # Track processed jobs to avoid duplicate state updates
        self._processed_jobs: set[str] = set()

    async def initialize(self, session: SessionMetadata) -> None:
        """Initialize dispatcher."""
        self.current_session = session
        await self.slash_handler.initialize(session)
        logger.info("Command dispatcher initialized")

    def set_current_shell(self, shell: Any) -> None:
        """Set the current interactive shell."""
        self.current_shell = shell
        if shell:
            logger.info("Entered shell mode")
        else:
            logger.info("Exited shell mode")

    async def process_command(self, user_input: str) -> bool:
        """Main command processing."""
        if not user_input.strip():
            return True

        try:
            # Check if we're in shell mode
            if self.current_shell:
                # Handle shell mode commands
                if user_input.lower() in ["exit", "quit"]:
                    # Exit shell mode
                    await self.current_shell.close()
                    self.set_current_shell(None)
                    self.ui_manager.print_info("Exited shell mode")
                    return True
                else:
                    # Execute command in shell
                    try:
                        output = await self.current_shell.execute(user_input)
                        if output:
                            self.ui_manager.print(output)
                    except Exception as e:
                        self.ui_manager.print_error(f"Shell command failed: {e}")
                    return True

            # Process slash commands
            if user_input.startswith("/"):
                return await self.slash_handler.handle_command(user_input)

            # AI natural language processing
            return await self._process_natural_language(user_input)

        except Exception as e:
            logger.error(f"Command processing error: {e}")
            self.ui_manager.print_error(f"Command processing error: {e}")
            return True

    async def _process_natural_language(self, user_input: str) -> bool:
        """Process natural language commands."""
        logger.debug(f"Processing natural language input: {user_input}")
        try:
            # Add to conversation history
            self.conversation_manager.add_user_message(user_input)

            # Get current state
            engagement_state = await self.state_manager.get_current_state()
            logger.debug(f"Current engagement state: mode={engagement_state.get_current_mode()}")

            # Detect exploit-related keywords (for logging)
            exploit_keywords = ["exploit", "attack", "verify", "check vulnerability", "use cve", "execute exploit"]
            is_exploit_request = any(keyword in user_input.lower() for keyword in exploit_keywords)

            if is_exploit_request:
                logger.debug("Detected exploit request - will generate plan for approval")

            # Plan generation
            self.ui_manager.print_info("Generating execution plan...")

            # Get timeout from config (default 120 seconds)
            from wish_core.config import get_llm_config

            llm_config = get_llm_config()
            timeout = llm_config.timeout
            logger.info(f"Starting plan generation with timeout={timeout}s, model={llm_config.model}")

            try:
                # Build context with retriever if available
                context = None
                if self.retriever:
                    try:
                        # Use ContextBuilder to create enriched context
                        from wish_ai.context import ContextBuilder

                        context_builder = ContextBuilder(retriever=self.retriever)
                        context = await context_builder.build_context(
                            user_input=user_input,
                            engagement_state=engagement_state,
                            conversation_history=self.conversation_manager.get_context_for_ai(),
                        )
                        logger.debug("Built context with knowledge base retrieval")
                    except Exception as e:
                        logger.warning(f"Failed to build context with retriever: {e}")
                        context = None

                # Create task with explicit timeout
                logger.debug("Calling plan_generator.generate_plan...")
                plan = await asyncio.wait_for(
                    self.plan_generator.generate_plan(
                        user_input=user_input,
                        engagement_state=engagement_state,
                        context=context,
                    ),
                    timeout=timeout,
                )
                logger.info("Plan generation completed successfully")
                logger.debug(f"Plan object: {plan}")
                logger.debug(f"Plan steps: {len(plan.steps) if plan else 'None'}")
            except TimeoutError:
                self.ui_manager.print_error(
                    f"Plan generation timed out after {timeout} seconds. "
                    "This might be due to network issues or OpenAI API problems. "
                    "You can increase the timeout by setting WISH_LLM_TIMEOUT environment variable."
                )
                return True
            except asyncio.CancelledError:
                self.ui_manager.print_error("Plan generation was cancelled")
                return True
            except Exception as e:
                # Show more detailed error information
                error_msg = str(e)
                if "api_key" in error_msg.lower():
                    self.ui_manager.print_error(
                        "API key error. Please check that your OpenAI API key is correctly set in:\n"
                        "  1. OPENAI_API_KEY environment variable, or\n"
                        "  2. ~/.wish/config.toml file"
                    )
                elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                    self.ui_manager.print_error(
                        "Network connection error. Please check:\n"
                        "  1. Your internet connection\n"
                        "  2. Any proxy/firewall settings\n"
                        "  3. OpenAI API status at https://status.openai.com/"
                    )
                else:
                    self.ui_manager.print_error(f"Plan generation failed: {error_msg}")
                logger.error(f"Plan generation error details: {e}", exc_info=True)
                return True

            logger.debug("Checking if plan is valid...")
            if not plan:
                logger.error("Plan is None or empty")
                self.ui_manager.print_error("Could not generate execution plan")
                return True

            # Check if this is a knowledge-based response (no steps)
            if not plan.steps:
                logger.info("Knowledge-based response - no steps to execute")
                # Display the information to the user
                self.ui_manager.print_info(f"[bold]{plan.description}[/bold]")
                if plan.rationale:
                    self.ui_manager.print("")
                    self.ui_manager.print(plan.rationale)
                # Add to conversation history
                self.conversation_manager.add_assistant_message(f"{plan.description}\n\n{plan.rationale}")
                return True

            # Display plan
            logger.info("Displaying plan to user...")
            self.ui_manager.print_plan(plan)

            # Plan approval
            logger.info("Requesting plan approval...")
            approved = await self.ui_manager.request_plan_approval(plan)

            if not approved:
                logger.info("Plan was not approved by user")
                self.ui_manager.print_info("Plan cancelled by user")
                return True

            # Execute plan
            logger.info("Executing approved plan...")
            await self._execute_plan(plan)

            return True

        except Exception as e:
            logger.error(f"Natural language processing error: {e}")
            self.ui_manager.print_error(f"Processing error: {e}")
            return True

    async def _execute_plan(self, plan: Plan) -> None:
        """Execute plan - parallel execution of all steps."""
        try:
            job_ids = []

            # Check for interactive commands
            interactive_steps = []
            for step in plan.steps:
                if step.command and is_interactive_command(step.command):
                    interactive_steps.append(step)

            # If there are interactive commands, handle them specially
            if interactive_steps:
                await self._handle_interactive_plan(plan, interactive_steps)
                return

            # Start all steps in parallel
            for _i, step in enumerate(plan.steps):
                job_id = self.ui_manager.job_manager.generate_job_id()
                job_ids.append(job_id)

                # Notify step execution start
                self.ui_manager.print_step_execution(step.tool_name, job_id)

                # Generate description: combine command name and purpose if available
                purpose = getattr(step, "purpose", None)
                if purpose and purpose != "No description available":
                    # Extract command name (up to first space)
                    cmd_name = step.command.split()[0] if step.command else step.tool_name
                    description = f"{cmd_name}: {purpose}"
                elif step.command:
                    # Display first 40 characters of command (add ... if longer)
                    description = step.command[:40] + "..." if len(step.command) > 40 else step.command
                else:
                    description = f"Executing {step.tool_name}"

                # Execute in parallel as background job
                await self.ui_manager.start_background_job(
                    job_id=job_id,
                    description=description,
                    job_coroutine=self._execute_step(step, job_id),
                    command=step.command,
                    tool_name=step.tool_name,
                    step_info={
                        "tool_name": step.tool_name,
                        "command": step.command,
                        "purpose": getattr(step, "purpose", "No description available"),
                        "parameters": getattr(step, "parameters", {}),
                    },
                )

                # Very short interval to avoid overwhelming the UI
                await asyncio.sleep(0.1)

            # Parallel execution completion message
            self.ui_manager.print_info(f"Started {len(job_ids)} jobs in parallel: {', '.join(job_ids)}")
            self.ui_manager.print_info("Use '/jobs' to monitor progress, '/status' for current state")

        except Exception as e:
            logger.error(f"Plan execution error: {e}")
            self.ui_manager.print_error(f"Plan execution error: {e}")

    async def _execute_step(self, step: PlanStep, job_id: str) -> dict[str, Any]:
        """Execute individual step."""
        try:
            # Expand variables in command
            command = await self._expand_command_variables(step.command)

            # Safety check: Re-verify that this command should run in background
            if is_interactive_command(command):
                error_msg = (
                    f"Interactive command '{command}' detected during background execution. "
                    "This command requires user interaction and cannot run in background."
                )
                logger.error(f"Background execution blocked for interactive command: {command}")
                self.ui_manager.print_error(error_msg)
                self.ui_manager.print_info(f"Please run this command manually: {command}")
                return {
                    "success": False,
                    "error": error_msg,
                    "job_id": job_id,
                    "output": error_msg,
                    "exit_code": 1,
                }

            # Execute tool
            result = await self.tool_executor.execute_command(
                command=command,
                tool_name=step.tool_name,
                timeout=300,  # 5 minute timeout
            )

            # Update state from result
            if result.success:
                # Update state on success
                await self._update_state_from_result(step, result)

                # Mark job as processed to avoid duplicate updates
                self._processed_jobs.add(job_id)

                # Completion notification
                self.ui_manager.print_step_completion(step.tool_name, job_id, True)

                logger.info(f"Step executed successfully: {step.tool_name}")
                return {
                    "success": True,
                    "result": result,
                    "job_id": job_id,
                    "output": result.stdout if hasattr(result, "stdout") else str(result),
                    "exit_code": 0,
                }
            else:
                # Failure notification
                self.ui_manager.print_step_completion(step.tool_name, job_id, False)
                self.ui_manager.print_error(f"Step failed: {step.tool_name} - {result.stderr}")

                logger.error(f"Step execution failed: {step.tool_name} - {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "job_id": job_id,
                    "output": result.stderr if hasattr(result, "stderr") else str(result),
                    "exit_code": 1,
                }

        except Exception as e:
            # Exception handling
            self.ui_manager.print_step_completion(step.tool_name, job_id, False)
            self.ui_manager.print_error(f"Step execution error: {step.tool_name} - {str(e)}")

            logger.error(f"Step execution exception: {step.tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "job_id": job_id,
                "output": f"Exception: {str(e)}",
                "exit_code": 2,
            }

    async def _update_state_from_result(self, step: PlanStep, result: Any) -> None:
        """Update state from execution result."""
        try:
            # Update state based on tool type
            if step.tool_name == "nmap":
                # Parse nmap results and update state
                await self._update_from_nmap_result(result)
            elif step.tool_name == "nikto":
                # Parse nikto results and update state
                await self._update_from_nikto_result(result)
            elif step.tool_name == "smbclient":
                # Parse smbclient results and update state
                await self._update_from_smbclient_result(result)
            elif step.tool_name == "enum4linux":
                # Parse enum4linux results and update state
                await self._update_from_enum4linux_result(result)
            # Add other tools similarly

        except Exception as e:
            logger.error(f"State update error: {e}")
            self.ui_manager.print_warning(f"Could not update state from {step.tool_name} result")

    async def handle_job_completion(self, job_id: str, job_info: JobInfo) -> None:
        """State update processing when job completes."""
        try:
            if job_info.status != JobStatus.COMPLETED:
                logger.debug(f"Job {job_id} did not complete successfully, skipping state update")
                return

            # Skip if already processed (avoid duplicate updates)
            if job_id in self._processed_jobs:
                logger.debug(f"Job {job_id} already processed, skipping duplicate update")
                return

            # Get step info from job
            step_info = job_info.step_info
            if not step_info:
                logger.warning(f"Job {job_id} has no step_info, cannot update state")
                return

            # Extract tool name and result
            tool_name = step_info.get("tool_name")
            if not tool_name:
                logger.warning(f"Job {job_id} has no tool_name in step_info")
                return

            # Get the job result
            result = job_info.result
            if not result:
                logger.warning(f"Job {job_id} has no result data")
                return

            # Create a mock PlanStep for compatibility
            from wish_ai.planning.models import RiskLevel, StepStatus

            mock_step = PlanStep(
                tool_name=tool_name,
                command=step_info.get("command", ""),
                purpose=step_info.get("purpose", ""),
                expected_result="",
                risk_level=RiskLevel.LOW,
                status=StepStatus.COMPLETED,
            )

            # Update state from result
            await self._update_state_from_result(mock_step, result)

            # Mark as processed
            self._processed_jobs.add(job_id)

            logger.info(f"State updated from job {job_id} completion")

        except Exception as e:
            logger.error(f"Error handling job completion for {job_id}: {e}")
            import traceback

            traceback.print_exc()

    async def _update_from_nmap_result(self, result: Any) -> None:
        """Update state from nmap result."""
        try:
            # Handle both ToolResult object and dict format
            if hasattr(result, "success"):
                # ToolResult object
                if not result.success or not result.stdout:
                    logger.warning("nmap result is empty or failed")
                    return
                stdout = result.stdout
            elif isinstance(result, dict):
                # Dict format from job completion
                if not result.get("success") or not result.get("output"):
                    logger.warning("nmap result is empty or failed")
                    return
                stdout = result.get("output", "")
            else:
                logger.warning(f"Unknown result format: {type(result)}")
                return

            # Parse nmap results
            if not self.nmap_parser.can_parse(stdout):
                logger.warning("nmap output format not recognized")
                return

            # Parse and update host information
            hosts = self.nmap_parser.parse_hosts(stdout)
            total_services = 0
            total_vulnerabilities = 0

            for host in hosts:
                await self.state_manager.update_hosts([host])
                logger.info(f"Updated host: {host.ip_address} ({host.status})")

                # Update service information
                for service in host.services:
                    total_services += 1
                    logger.info(f"Found service: {service.port}/{service.protocol} {service.service_name}")

                # Automatic vulnerability detection
                vulnerabilities = self.vulnerability_detector.detect_vulnerabilities(host)
                for vuln in vulnerabilities:
                    await self.state_manager.add_finding(vuln)
                    total_vulnerabilities += 1
                    primary_cve = vuln.cve_ids[0] if vuln.cve_ids else "No CVE"
                    logger.info(f"Detected vulnerability: {primary_cve} - {vuln.title}")

                    # Special UI notification for critical vulnerabilities
                    if vuln.severity == "critical":
                        self.ui_manager.print_warning(f"🚨 Critical vulnerability detected: {primary_cve}")
                        self.ui_manager.print_info(f"   {vuln.title} on {host.ip_address}")

                        # Display exploit suggestions
                        suggestions = self.vulnerability_detector.get_exploit_suggestions(primary_cve)
                        if suggestions:
                            self.ui_manager.print_info("   Exploit suggestions:")
                            for suggestion in suggestions:
                                self.ui_manager.print_info(f"   - {suggestion}")

            # Parse and update vulnerability findings from nmap scripts
            script_findings = self.nmap_parser.parse_findings(stdout)
            for finding in script_findings:
                await self.state_manager.add_finding(finding)
                logger.info(f"Added script finding: {finding.title}")

            # UI update notification
            self.ui_manager.print_info(
                f"State updated: {len(hosts)} hosts, {total_services} services, {total_vulnerabilities} vulnerabilities"
            )

            # Display AI hint message (demo scenario style)
            if total_services > 0:
                self.ui_manager.show_info(
                    "AI Hint: Scan complete. I found some interesting services. "
                    "I will now check for known public exploits."
                )

                # Display vulnerability detection execution
                self.ui_manager.show_progress("Analyzing services for vulnerabilities...")
                await asyncio.sleep(1)  # Realistic delay

                if total_vulnerabilities > 0:
                    self.ui_manager.show_success("Analysis complete. I found critical vulnerabilities:")

                    # List detected vulnerabilities
                    for host in hosts:
                        vulns = self.vulnerability_detector.detect_vulnerabilities(host)
                        for vuln in vulns:
                            if vuln.cve_ids:
                                cve_id = vuln.cve_ids[0]
                                self.ui_manager.print_info(f"    - Service: {vuln.title}")
                                self.ui_manager.print_info(f"    - Vulnerability: {cve_id} - Remote Command Execution")

                                # Automatically record critical vulnerabilities
                                if vuln.severity == "critical":
                                    self.ui_manager.show_success(
                                        f"Critical finding '{cve_id}' automatically recorded. Use /findings to view."
                                    )
                else:
                    self.ui_manager.show_info("No critical vulnerabilities detected in scanned services.")

        except Exception as e:
            logger.error(f"Failed to update state from nmap result: {e}")
            self.ui_manager.print_warning(f"Could not fully update state from nmap result: {e}")

    async def _update_from_nikto_result(self, result: Any) -> None:
        """Update state from nikto result."""
        # Parse nikto results and update state (simplified)
        logger.debug("Updating state from nikto result")
        # In actual implementation, use nikto parser to analyze results
        pass

    async def _update_from_smbclient_result(self, result: Any) -> None:
        """Update state from smbclient result."""
        try:
            # Handle both ToolResult object and dict format
            if hasattr(result, "success"):
                # ToolResult object
                if not result.success or not result.stdout:
                    logger.warning("smbclient result is empty or failed")
                    return
                stdout = result.stdout
            elif isinstance(result, dict):
                # Dict format from job completion
                if not result.get("success") or not result.get("output"):
                    logger.warning("smbclient result is empty or failed")
                    return
                stdout = result.get("output", "")
            else:
                logger.warning(f"Unknown smbclient result format: {type(result)}")
                return

            # Parse using smbclient parser
            if not self.smbclient_parser.can_parse(stdout):
                logger.warning("smbclient output format not recognized")
                return

            # Extract and update host information
            hosts = self.smbclient_parser.parse_hosts(stdout)
            for host in hosts:
                # Get SMB metadata for this host
                metadata = self.smbclient_parser.get_metadata(stdout)

                # Create SMB info from metadata
                from wish_models import SMBInfo, SMBShare

                smb_shares = []
                for share_data in metadata.get("shares", []):
                    smb_share = SMBShare(
                        name=share_data["name"],
                        type=share_data["type"],
                        comment=share_data["comment"],
                        accessible=None,
                        writable=None,
                        discovered_by="smbclient",
                    )
                    smb_shares.append(smb_share)

                smb_info = SMBInfo(
                    workgroup=metadata.get("workgroup"),
                    domain=None,
                    server_name=None,
                    os_name=None,
                    os_version=None,
                    shares=smb_shares,
                    anonymous_access="Anonymous login successful" in stdout,
                    null_session=False,
                    discovered_by="smbclient",
                )

                # Update host with SMB info
                host.smb_info = smb_info

                await self.state_manager.update_hosts([host])
                logger.info(f"Updated host with SMB info: {host.ip_address}")

            # Extract and add findings
            findings = self.smbclient_parser.parse_findings(stdout)
            for finding in findings:
                await self.state_manager.add_finding(finding)
                logger.info(f"Added SMB finding: {finding.title}")

            # Update UI with summary
            shares_count = len(metadata.get("shares", []))
            self.ui_manager.print_info(
                f"SMB state updated: {len(hosts)} hosts, {shares_count} shares, {len(findings)} findings"
            )

        except Exception as e:
            logger.error(f"Failed to update state from smbclient result: {e}")
            self.ui_manager.print_warning(f"Could not fully update state from smbclient result: {e}")

    async def _update_from_enum4linux_result(self, result: Any) -> None:
        """Update state from enum4linux result."""
        try:
            # Handle both ToolResult object and dict format
            if hasattr(result, "success"):
                # ToolResult object
                if not result.success or not result.stdout:
                    logger.warning("enum4linux result is empty or failed")
                    return
                stdout = result.stdout
            elif isinstance(result, dict):
                # Dict format from job completion
                if not result.get("success") or not result.get("output"):
                    logger.warning("enum4linux result is empty or failed")
                    return
                stdout = result.get("output", "")
            else:
                logger.warning(f"Unknown enum4linux result format: {type(result)}")
                return

            # Parse using enum4linux parser
            if not self.enum4linux_parser.can_parse(stdout):
                logger.warning("enum4linux output format not recognized")
                return

            # Extract and update host information
            hosts = self.enum4linux_parser.parse_hosts(stdout)
            for host in hosts:
                # Get enum4linux metadata
                metadata = self.enum4linux_parser.get_metadata(stdout)

                # Create/update SMB info from metadata
                from wish_models import SMBInfo

                domain_info = metadata.get("domain_info", {})
                smb_info = SMBInfo(
                    workgroup=domain_info.get("workgroup"),
                    domain=domain_info.get("workgroup"),  # Often same as workgroup
                    server_name=None,
                    os_name=domain_info.get("os"),
                    os_version=None,
                    anonymous_access=False,
                    null_session=False,
                    discovered_by="enum4linux",
                )

                # Update host with SMB info
                host.smb_info = smb_info

                await self.state_manager.update_hosts([host])
                logger.info(f"Updated host with enum4linux info: {host.ip_address}")

            # Extract and add findings
            findings = self.enum4linux_parser.parse_findings(stdout)
            for finding in findings:
                await self.state_manager.add_finding(finding)
                logger.info(f"Added enum4linux finding: {finding.title}")

            # Update UI with summary
            users_count = len(metadata.get("users", []))
            groups_count = len(metadata.get("groups", []))
            self.ui_manager.print_info(
                f"enum4linux state updated: {len(hosts)} hosts, {users_count} users, "
                f"{groups_count} groups, {len(findings)} findings"
            )

        except Exception as e:
            logger.error(f"Failed to update state from enum4linux result: {e}")
            self.ui_manager.print_warning(f"Could not fully update state from enum4linux result: {e}")

    async def _handle_exploit_request(self, user_input: str, engagement_state: Any) -> bool:
        """Dedicated processing for exploit requests."""
        try:
            # Search for known vulnerabilities
            available_vulns = []
            for finding in engagement_state.findings.values():
                if finding.cve_ids:
                    for cve_id in finding.cve_ids:
                        if cve_id in self.exploit_engine.list_available_exploits():
                            available_vulns.append(finding)
                            break  # Add if any match is found

            if not available_vulns:
                self.ui_manager.print_warning("No exploitable vulnerabilities found in current engagement state")
                return False

            # Use single vulnerability if available
            if len(available_vulns) == 1:
                vuln = available_vulns[0]
                # Use first CVE ID
                primary_cve = vuln.cve_ids[0] if vuln.cve_ids else None
                if not primary_cve:
                    self.ui_manager.print_error("No CVE ID found in vulnerability")
                    return False

                self.ui_manager.print_info(f"Using vulnerability: {primary_cve} - {vuln.title}")

                # Get target IP
                target_ip = self._extract_target_ip(engagement_state)
                if not target_ip:
                    self.ui_manager.print_error("No target IP found in engagement state")
                    return False

                # Determine command
                command = self._extract_command_from_input(user_input)

                # Vulnerability verification
                if "verify" in user_input.lower():
                    self.ui_manager.show_progress("Verifying RCE vulnerability...")
                    result = await self.exploit_engine.verify_vulnerability(primary_cve, target_ip, command)
                    self._display_exploit_result(result, "Verification")
                else:
                    # Execute exploit
                    self.ui_manager.show_progress(f"Executing exploit with command: {command}...")
                    result = await self.exploit_engine.execute_exploit(primary_cve, target_ip, command)
                    self._display_exploit_result(result, "Exploitation")

                return True
            else:
                # If multiple vulnerabilities available, ask for selection
                self.ui_manager.print_info("Multiple vulnerabilities available:")
                for i, vuln in enumerate(available_vulns, 1):
                    primary_cve = vuln.cve_ids[0] if vuln.cve_ids else "No CVE"
                    self.ui_manager.print_info(f"  {i}. {primary_cve} - {vuln.title}")
                self.ui_manager.print_info("Please specify which vulnerability to exploit")
                return False

        except Exception as e:
            logger.error(f"Exploit handling error: {e}")
            self.ui_manager.print_error(f"Exploit handling error: {e}")
            return False

    def _extract_target_ip(self, engagement_state: Any) -> str | None:
        """Extract target IP from engagement state."""
        if engagement_state.hosts:
            # Use IP of first host
            return list(engagement_state.hosts.values())[0].ip_address  # type: ignore[no-any-return]
        return None

    def _extract_command_from_input(self, user_input: str) -> str:
        """Extract command from user input."""
        # Simple command extraction logic
        if "whoami" in user_input.lower():
            return "whoami"
        elif "pwd" in user_input.lower():
            return "pwd"
        elif "ls" in user_input.lower():
            return "ls"
        elif "uname" in user_input.lower():
            return "uname -a"
        else:
            return "id"  # Default

    def _display_exploit_result(self, result: dict[str, Any], operation: str) -> None:
        """Display exploit result."""
        if result.get("success"):
            self.ui_manager.show_success(f"{operation} successful!")
            if result.get("output"):
                output = result["output"].strip()
                # Demo scenario style output format
                self.ui_manager.show_success("Exploit successful! Command output:")
                self.ui_manager.print(f"    {output}")
            if result.get("verified"):
                self.ui_manager.show_info("Vulnerability is confirmed exploitable!")

                # Record as Finding (implementation)
                import asyncio

                from wish_models.finding import Finding

                finding = Finding(
                    title=f"Successfully exploited {result.get('cve_id', 'vulnerability')}",
                    description=f"RCE verified on {result.get('target', 'target')} - command execution successful",
                    category="vulnerability",
                    severity="critical",
                    target_type="host",
                    discovered_by="exploit_verification",
                    evidence=f"Command output:\n{result.get('output', 'No output')}",
                    cve_ids=[str(result.get("cve_id"))] if result.get("cve_id") else [],
                    host_id=result.get("target"),
                    service_id=None,
                    url=None,
                    status="confirmed",
                    recommendation="System compromised - immediate action required",
                )

                # Add Finding asynchronously
                asyncio.create_task(self.state_manager.add_finding(finding))
                logger.info(f"Added exploitation finding for {result.get('cve_id')}")
        else:
            self.ui_manager.print_error(f"{operation} failed: {result.get('error', 'Unknown error')}")

    async def _expand_command_variables(self, command: str) -> str:
        """Expand variables in command."""
        try:
            # Get current state
            state = await self.state_manager.get_current_state()

            # Replace target - use first in-scope target
            if "target" in command:
                # Get in-scope targets
                targets = [t for t in state.targets.values() if t.in_scope]
                if targets:
                    # Use IP address of first target
                    target_ip = targets[0].scope
                    command = command.replace("target", target_ip)
                    logger.debug(f"Replaced 'target' with '{target_ip}' in command")
                else:
                    logger.warning("No targets in scope for variable expansion")

            return command
        except Exception as e:
            logger.error(f"Error expanding command variables: {e}")
            # Return original command on error
            return command

    async def _handle_interactive_plan(self, plan: Plan, interactive_steps: list[PlanStep]) -> None:
        """Handle plan with interactive commands."""
        # Warn about interactive commands
        self.ui_manager.print_warning("This plan contains interactive commands that cannot be executed automatically.")
        self.ui_manager.print_info("Instead, I'll show you examples and guidance for using these commands.\n")

        # Show interactive command examples FIRST to allow immediate user action
        for step in interactive_steps:
            command = await self._expand_command_variables(step.command)
            await self._show_interactive_command_examples(command, step)

        # Execute non-interactive steps in parallel background
        non_interactive_steps = [s for s in plan.steps if s not in interactive_steps]
        if non_interactive_steps:
            self.ui_manager.print_info(
                f"Starting {len(non_interactive_steps)} non-interactive commands in background..."
            )

            job_ids = []
            for step in non_interactive_steps:
                job_id = self.ui_manager.job_manager.generate_job_id()
                job_ids.append(job_id)

                # Create description for the job
                purpose = getattr(step, "purpose", None)
                if purpose and purpose != "No description available":
                    cmd_name = step.command.split()[0] if step.command else step.tool_name
                    description = f"{cmd_name}: {purpose}"
                elif step.command:
                    description = step.command[:40] + "..." if len(step.command) > 40 else step.command
                else:
                    description = f"Executing {step.tool_name}"

                # Start background job
                await self.ui_manager.start_background_job(
                    job_id=job_id,
                    description=description,
                    job_coroutine=self._execute_step(step, job_id),
                    command=step.command,
                    tool_name=step.tool_name,
                    step_info={
                        "tool_name": step.tool_name,
                        "command": step.command,
                        "purpose": getattr(step, "purpose", "No description available"),
                        "parameters": getattr(step, "parameters", {}),
                    },
                )

                # Brief interval to avoid overwhelming
                await asyncio.sleep(0.1)

            self.ui_manager.print_info(f"Started background jobs: {', '.join(job_ids)}")
            self.ui_manager.print_info("Use '/jobs' to monitor progress while using interactive commands")

    async def _show_interactive_command_examples(self, command: str, step: PlanStep) -> None:
        """Show examples and guidance for interactive commands."""
        # Extract base command
        base_cmd = command.split()[0] if command else ""
        base_cmd = os.path.basename(base_cmd)
        desc = get_command_description(command)

        # Display command information
        self.ui_manager.print("\n[bold]Interactive Command Information[/bold]")
        self.ui_manager.print(f"Command: [cyan]{command}[/cyan]")
        self.ui_manager.print(f"Type: {desc}")
        self.ui_manager.print(f"Purpose: {step.purpose}\n")

        # Try to get examples from knowledge base
        examples = await self._get_command_examples_from_knowledge(base_cmd)

        if examples:
            self.ui_manager.print("[bold]Examples from Knowledge Base:[/bold]")
            for example in examples:
                self.ui_manager.print(f"  • {example}")
            self.ui_manager.print("")

        # Show common usage patterns based on command type
        usage_patterns = self._get_usage_patterns(base_cmd, command)
        if usage_patterns:
            self.ui_manager.print("[bold]Common Usage Patterns:[/bold]")
            for pattern in usage_patterns:
                self.ui_manager.print(f"  • [cyan]{pattern}[/cyan]")
            self.ui_manager.print("")

        # Provide manual execution guidance
        self.ui_manager.print("[yellow]To execute this command manually:[/yellow]")
        self.ui_manager.print("1. Open a new terminal window")
        self.ui_manager.print(f"2. Run: [cyan]{command}[/cyan]")
        self.ui_manager.print("3. Interact with the tool as needed")
        self.ui_manager.print("4. Return to wish when done\n")

        # Show tips for the specific command type
        tips = self._get_command_tips(base_cmd)
        if tips:
            self.ui_manager.print("[bold]Tips:[/bold]")
            for tip in tips:
                self.ui_manager.print(f"  💡 {tip}")
            self.ui_manager.print("")

    async def _get_command_examples_from_knowledge(self, command: str) -> list[str]:
        """Retrieve command examples from knowledge base."""
        if not self.retriever:
            return []

        try:
            # Query knowledge base for command examples
            query = f"{command} examples usage penetration testing"
            results = await self.retriever.search(query, limit=3)

            examples = []
            for result in results:
                # Extract example commands from results
                if "example_commands" in result:
                    examples.extend(result["example_commands"])
                elif "text" in result and command in result["text"]:
                    # Try to extract command patterns from text
                    lines = result["text"].split("\n")
                    for line in lines:
                        if command in line and ("$" in line or ">" in line or "#" in line):
                            # Clean up the command
                            cmd = line.strip().lstrip("$>#").strip()
                            if cmd and cmd not in examples:
                                examples.append(cmd)

            return examples[:5]  # Return up to 5 examples
        except Exception as e:
            logger.warning(f"Failed to retrieve examples from knowledge base: {e}")
            return []

    def _get_usage_patterns(self, base_cmd: str, full_command: str) -> list[str]:
        """Get common usage patterns for interactive commands."""
        patterns = {
            "ssh": [
                "ssh user@hostname",
                "ssh -p 2222 user@hostname  # Custom port",
                "ssh -i keyfile user@hostname  # With key file",
                "ssh -D 1080 user@hostname  # Dynamic port forwarding",
            ],
            "ftp": [
                "ftp hostname",
                "ftp -p hostname  # Passive mode",
                "ftp ftp://user:pass@hostname  # With credentials",
            ],
            "telnet": [
                "telnet hostname port",
                "telnet hostname 23  # Default telnet port",
                "telnet hostname 80  # Test HTTP connectivity",
            ],
            "mysql": [
                "mysql -h hostname -u username -p",
                "mysql -h hostname -P 3306 -u root -p  # Specify port",
                "mysql -h hostname -u username -p database_name",
            ],
            "nc": [
                "nc -nv hostname port  # Verbose connection",
                "nc -lvnp 4444  # Listen on port",
                "nc hostname port < file  # Send file",
            ],
            "python": [
                "python -c 'import pty; pty.spawn(\"/bin/bash\")'  # Spawn shell",
                "python -m http.server 8000  # Quick HTTP server",
                "python -m SimpleHTTPServer 8000  # Python 2",
            ],
            "msfconsole": [
                "msfconsole -q  # Quiet mode (no banner)",
                "msfconsole -x 'use exploit/...'  # Run command",
                "msfconsole -r script.rc  # Run resource script",
            ],
        }

        return patterns.get(base_cmd, [])

    def _get_command_tips(self, base_cmd: str) -> list[str]:
        """Get tips for using interactive commands."""
        tips = {
            "ssh": [
                "Use -v for verbose output to debug connection issues",
                "Add 'StrictHostKeyChecking no' to ~/.ssh/config for testing (not production!)",
                "Use ssh-keygen to generate key pairs for passwordless authentication",
            ],
            "ftp": [
                "Anonymous login often uses 'anonymous' as username and email as password",
                "Use 'binary' mode for transferring non-text files",
                "Try 'passive' mode if having connection issues through firewalls",
            ],
            "mysql": [
                "Check for default credentials like root with no password",
                "Use --batch mode for non-interactive execution",
                "SHOW DATABASES; and SHOW TABLES; are useful first commands",
            ],
            "nc": [
                "Use -z for port scanning without sending data",
                "Combine with other tools using pipes for powerful workflows",
                "Use -u for UDP connections",
            ],
            "python": [
                "Interactive Python shells are great for testing payloads",
                "Use sys.version to check Python version",
                "Import os and subprocess for system interaction",
            ],
            "msfconsole": [
                "Use 'search' command to find relevant exploits",
                "Set RHOSTS for target hosts, LHOST for your IP",
                "Use 'show options' to see required parameters",
            ],
        }

        return tips.get(base_cmd, [])

    async def shutdown(self) -> None:
        """Dispatcher shutdown processing."""
        logger.info("Shutting down command dispatcher...")
        await self.slash_handler.shutdown()
        logger.info("Command dispatcher shutdown complete")
