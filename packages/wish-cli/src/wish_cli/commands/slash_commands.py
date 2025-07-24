"""Slash command handlers for wish-cli."""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from wish_core.session import SessionManager
from wish_core.state.manager import StateManager
from wish_models.engagement import EngagementState, Target
from wish_models.finding import Finding
from wish_models.session import SessionMetadata
from wish_tools.execution.executor import ToolExecutor

from wish_cli.ui.ui_manager import WishUIManager

logger = logging.getLogger(__name__)


class SlashCommandHandler:
    """Slash command handler."""

    def __init__(
        self,
        ui_manager: WishUIManager,
        state_manager: StateManager,
        session_manager: SessionManager,
        tool_executor: ToolExecutor,
        c2_connector: Any | None = None,
    ):
        self.ui_manager = ui_manager
        self.state_manager = state_manager
        self.session_manager = session_manager
        self.tool_executor = tool_executor
        self.c2_connector = c2_connector

        # Command map
        self.commands: dict[str, Callable] = {
            "help": self._help_command,
            "?": self._help_command,
            "status": self._status_command,
            "s": self._status_command,
            "mode": self._mode_command,
            "m": self._mode_command,
            "scope": self._scope_command,
            "findings": self._findings_command,
            "f": self._findings_command,
            "jobs": self._jobs_command,
            "j": self._jobs_command,
            "logs": self._logs_command,
            "log": self._logs_command,
            "stop": self._stop_command,
            "kill": self._stop_command,
            "k": self._stop_command,
            "sliver": self._sliver_command,
            "clear": self._clear_command,
            "history": self._history_command,
            "config": self._config_command,
        }

        # Session information
        self.current_session: SessionMetadata | None = None

        # Command dispatcher reference (set later)
        self.command_dispatcher: Any = None

    async def initialize(self, session: SessionMetadata) -> None:
        """Initialize handler."""
        self.current_session = session
        logger.info("Slash command handler initialized")

    async def handle_command(self, command_line: str) -> bool:
        """Process command."""
        if not command_line.startswith("/"):
            return False

        # Parse command line
        parts = command_line[1:].split()
        if not parts:
            return False

        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Execute command
        if command in self.commands:
            try:
                await self.commands[command](args)
                return True
            except Exception as e:
                logger.error(f"Slash command error: {e}")
                self.ui_manager.print_error(f"Command error: {e}")
                return True
        else:
            self.ui_manager.print_error(f"Unknown command: /{command}")
            return True

    async def _help_command(self, args: list[str]) -> None:
        """Help command."""
        logger.info("Help command called")
        if args:
            # Help for specific command
            command = args[0].lower()
            await self._show_command_help(command)
        else:
            # Help for all commands
            await self._show_general_help()

    async def _show_general_help(self) -> None:
        """Display general help."""
        logger.info("Showing general help")
        help_text = """
[bold]wish - AI-powered Penetration Testing Command Center[/bold]

[bold blue]Slash Commands:[/bold blue]
  /help          : Show this help
  /status        : Show current engagement status
  /mode <mode>   : Change mode (recon/enum/exploit/report)
  /scope add <target> : Add target to scope
  /scope remove <target> : Remove target from scope
  /findings      : Show current findings
  /jobs          : Show running jobs
  /logs <job_id> : Show logs for a specific job
  /stop <job_id> : Stop a running job
  /sliver        : Interact with Sliver C2
  /config        : Show configuration
  /history       : Show command history
  /clear         : Clear screen

[bold blue]Natural Language:[/bold blue]
  Simply type what you want to do:
  - "scan the target"
  - "enumerate web directories"
  - "check for SQL injection"
  - "deploy sliver implant"

[bold blue]Keyboard Shortcuts:[/bold blue]
  Ctrl+C (once)  : Clear current input
  Ctrl+C (twice) : Exit wish
  Tab            : Command completion
  ↑/↓           : Command history
        """

        self.ui_manager.print(Panel(help_text, title="[bold]Help[/bold]", border_style="blue"))

    async def _show_command_help(self, command: str) -> None:
        """Display help for specific command."""
        help_texts = {
            "status": """
[bold]/status[/bold] - Show current engagement status

Usage: /status [--raw]

Shows a hierarchical view of the current engagement state including:
- Target scope
- Discovered hosts
- Open ports and services
- Findings
- Running jobs

Options:
  --raw    Output raw text without pager
            """,
            "mode": """
[bold]/mode[/bold] - Change current mode

Usage: /mode [recon|enum|exploit|report]

Modes:
  recon    : Reconnaissance phase
  enum     : Enumeration phase
  exploit  : Exploitation phase
  report   : Reporting phase

Without arguments, shows current mode.
            """,
            "scope": """
[bold]/scope[/bold] - Manage target scope

Usage:
  /scope                    Show current scope
  /scope add <target>       Add target to scope
  /scope remove <target>    Remove target from scope

Examples:
  /scope add 10.0.0.0/24
  /scope add example.com
  /scope remove 10.0.0.1
            """,
        }

        help_text = help_texts.get(command, f"No help available for /{command}")
        self.ui_manager.print(Panel(help_text, title=f"Help: /{command}", border_style="blue"))

    async def _status_command(self, args: list[str]) -> None:
        """Status command."""
        try:
            # Get current state
            engagement_state = await self.state_manager.get_current_state()

            # Build demo scenario format output
            status_output = self._build_demo_status_output(engagement_state)

            # Output decorated with Rich Panel (displayed via Textual RichLog)
            status_panel = Panel(status_output, title="Engagement Status", border_style="cyan")
            self.ui_manager.print(status_panel)

        except Exception as e:
            logger.error(f"Status command error: {e}")
            self.ui_manager.print_error(f"Could not retrieve status: {e}")

    def _build_demo_status_output(self, engagement_state: EngagementState) -> str:
        """Build demo scenario format status output."""
        lines = []

        # TARGETS
        lines.append("[bold]TARGETS:[/bold]")
        if engagement_state.targets:
            for target in engagement_state.targets.values():
                lines.append(f"└─ {target.scope}")

                # Search for hosts related to target
                host = None
                if engagement_state.hosts:
                    for h in engagement_state.hosts.values():
                        if h.ip_address == target.scope:
                            host = h
                            break

                if host:
                    # PORTS
                    lines.append("   ├─ [bold]PORTS:[/bold]")
                    if hasattr(host, "services") and host.services:
                        for service in host.services:
                            service_info = f"{service.port}/{service.protocol}"
                            if hasattr(service, "service_name") and service.service_name:
                                service_info += f" ({service.service_name}"
                                if hasattr(service, "product") and service.product:
                                    service_info += f", {service.product}"
                                    if hasattr(service, "version") and service.version:
                                        service_info += f" {service.version}"
                                service_info += ")"
                            lines.append(f"   │  ├─ {service_info}")

                    # VULNERABILITIES
                    vulns = self._get_host_vulnerabilities(host, engagement_state.findings)
                    if vulns:
                        lines.append("   └─ [bold]VULNERABILITIES:[/bold]")
                        for vuln in vulns:
                            vuln_info = f"{vuln.title}"
                            if vuln.cve_ids:
                                vuln_info = f"{vuln.cve_ids[0]} ({vuln.title})"
                            lines.append(f"      └─ {vuln_info}")
        else:
            lines.append("└─ No targets defined")

        return "\n".join(lines)

    def _build_status_tree(self, engagement_state: EngagementState) -> Tree:
        """Build status tree."""
        root = Tree("[bold cyan]ENGAGEMENT STATUS[/bold cyan]")

        # Targets
        targets_branch = root.add("[bold]TARGETS:[/bold]")
        if engagement_state.targets:
            for target in engagement_state.targets.values():
                targets_branch.add(f"└─ [cyan]{target.scope}[/cyan] ({target.scope_type})")
        else:
            targets_branch.add("└─ [dim]No targets defined[/dim]")

        # Hosts
        hosts_branch = root.add("\n[bold]HOSTS:[/bold]")
        if engagement_state.hosts:
            for host in engagement_state.hosts.values():
                host_branch = hosts_branch.add(f"└─ [green]{host.ip_address}[/green]")
                if hasattr(host, "services") and host.services:
                    # Display ports and services
                    ports_branch = host_branch.add("├─ [bold]PORTS:[/bold]")
                    for service in host.services:
                        service_info = f"{service.port}/{service.protocol}"
                        if hasattr(service, "service_name") and service.service_name:
                            service_info += f" ({service.service_name}"
                            if hasattr(service, "product") and service.product:
                                service_info += f", {service.product}"
                            service_info += ")"
                        ports_branch.add(f"│  └─ [blue]{service_info}[/blue]")

                    # Display vulnerability information
                    vulns = self._get_host_vulnerabilities(host, engagement_state.findings)
                    if vulns:
                        vuln_branch = host_branch.add("└─ [bold]VULNERABILITIES:[/bold]")
                        for vuln in vulns:
                            vuln_info = f"[red]{vuln.severity.upper()}[/red] - {vuln.title}"
                            if vuln.cve_ids:
                                vuln_info = f"{vuln.cve_ids[0]} {vuln_info}"
                            vuln_branch.add(f"   └─ {vuln_info}")
        else:
            hosts_branch.add("└─ [dim]No hosts discovered[/dim]")

        # Findings
        findings_branch = root.add("\n[bold]FINDINGS:[/bold]")
        if engagement_state.findings:
            # Sort by severity
            sorted_findings = sorted(
                engagement_state.findings.values(),
                key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f.severity.lower(), 4),
            )
            for finding in sorted_findings:
                severity_color = {"critical": "red", "high": "red", "medium": "yellow", "low": "blue"}.get(
                    finding.severity.lower(), "white"
                )

                icon = {"critical": "[❌]", "high": "[⚠️]", "medium": "[ℹ]", "low": "[✔]"}.get(
                    finding.severity.lower(), "[•]"
                )

                finding_info = (
                    f"{icon} [{severity_color}]{finding.severity.upper()}[/{severity_color}] - {finding.title}"
                )
                if finding.cve_ids:
                    finding_info = f"{finding.cve_ids[0]}: {finding_info}"
                findings_branch.add(f"└─ {finding_info}")
        else:
            findings_branch.add("└─ [dim]No findings[/dim]")

        # Collected data
        data_branch = root.add("\n[bold]COLLECTED DATA:[/bold]")
        if engagement_state.collected_data:
            for data_type, _data_item in engagement_state.collected_data.items():
                data_branch.add(f"└─ [magenta]{data_type}[/magenta]")
        else:
            data_branch.add("└─ [dim]No data collected[/dim]")

        return root

    def _get_host_vulnerabilities(self, host: Any, findings: dict[str, Finding]) -> list[Finding]:
        """Get vulnerabilities related to host."""
        host_vulns = []
        for finding in findings.values():
            # Check if host IP is included in finding description or title
            if (
                host.ip_address in finding.description
                or host.ip_address in finding.title
                or (hasattr(finding, "affected_hosts") and host.ip_address in getattr(finding, "affected_hosts", []))
            ):
                host_vulns.append(finding)
        return host_vulns

    async def _mode_command(self, args: list[str]) -> None:
        """Mode command."""
        if not args:
            # Display current mode
            current_mode = self.current_session.current_mode if self.current_session else "recon"
            self.ui_manager.print(f"Current mode: [bold blue]{current_mode}[/bold blue]")
            return

        # Change mode
        new_mode = args[0].lower()
        valid_modes = ["recon", "enum", "exploit", "report"]

        if new_mode not in valid_modes:
            self.ui_manager.print_error(f"Invalid mode: {new_mode}. Valid modes: {', '.join(valid_modes)}")
            return

        if self.current_session:
            self.current_session.change_mode(new_mode)
            try:
                # Get current engagement state to save
                current_state = await self.state_manager.get_current_state()
                await self.session_manager.save_session(current_state)
            except Exception as e:
                logger.error(f"Failed to save session: {e}")
            self.ui_manager.print(f"Mode changed to [bold blue]{new_mode}[/bold blue]")
        else:
            self.ui_manager.print_error("No active session")

    async def _scope_command(self, args: list[str]) -> None:
        """Scope command."""
        if not args:
            # Display current scope
            engagement_state = await self.state_manager.get_current_state()
            if engagement_state.targets:
                scope_table = Table(title="Target Scope")
                scope_table.add_column("Target", style="cyan")
                scope_table.add_column("Type", style="magenta")

                for target in engagement_state.targets.values():
                    scope_table.add_row(target.scope, target.scope_type)

                self.ui_manager.print(scope_table)
            else:
                self.ui_manager.print("[dim]No scope defined[/dim]")
            return

        # Scope operations
        operation = args[0].lower()
        if operation == "add" and len(args) > 1:
            target_scope = args[1]
            try:
                # Create new target - determine appropriate scope type
                if "/" in target_scope:
                    # CIDR notation
                    scope_type = "cidr"
                elif target_scope.replace(".", "").isdigit():
                    # IP address
                    scope_type = "ip"
                elif target_scope.startswith("http://") or target_scope.startswith("https://"):
                    # URL
                    scope_type = "url"
                else:
                    # Domain name
                    scope_type = "domain"

                target = Target(
                    scope=target_scope,
                    scope_type=scope_type,  # type: ignore[arg-type]
                    name=None,
                    description=None,
                    in_scope=True,
                    engagement_rules=None,
                )

                # Add to state manager
                await self.state_manager.add_target(target)
                self.ui_manager.print(f"Added [cyan]{target_scope}[/cyan] to scope")
            except Exception as e:
                logger.error(f"Failed to add target: {e}")
                self.ui_manager.print_error(f"Could not add target: {e}")
        elif operation == "remove" and len(args) > 1:
            target_scope = args[1]
            try:
                # Remove from state manager
                await self.state_manager.remove_target(target_scope)
                self.ui_manager.print(f"Removed [cyan]{target_scope}[/cyan] from scope")
            except Exception as e:
                logger.error(f"Failed to remove target: {e}")
                self.ui_manager.print_error(f"Could not remove target: {e}")
        else:
            self.ui_manager.print_error("Usage: /scope [add|remove] <target>")

    async def _findings_command(self, args: list[str]) -> None:
        """Findings command."""
        if args and args[0].lower() == "add":
            # Add finding
            if len(args) < 2:
                self.ui_manager.print_error("Usage: /findings add <description>")
                return

            description = " ".join(args[1:])
            try:
                # Create new finding
                finding = Finding(
                    title="Manual Finding",
                    description=description,
                    category="other",  # 'manual' is not a valid category
                    severity="info",
                    target_type="host",  # 'manual' is not a valid target_type
                    discovered_by="user",
                    evidence=description,
                    host_id=None,
                    service_id=None,
                    url=None,
                    status="new",
                    recommendation="Review and investigate this finding",
                )

                # Add to state manager
                await self.state_manager.add_finding(finding)
                self.ui_manager.print(f"Added finding: [cyan]{description}[/cyan]")
            except Exception as e:
                logger.error(f"Failed to add finding: {e}")
                self.ui_manager.print_error(f"Could not add finding: {e}")
            return

        # Display findings
        engagement_state = await self.state_manager.get_current_state()

        if not engagement_state.findings:
            self.ui_manager.print("[dim]No findings[/dim]")
            return

        # Findings table
        findings_table = Table(title="Security Findings")
        findings_table.add_column("Severity", style="red")
        findings_table.add_column("Title", style="bold")
        findings_table.add_column("Category", style="magenta")
        findings_table.add_column("Description", style="white")

        for finding in engagement_state.findings.values():
            findings_table.add_row(
                finding.severity,
                finding.title,
                finding.category,
                finding.description[:50] + "..." if len(finding.description) > 50 else finding.description,
            )

        self.ui_manager.print(findings_table)

    async def _jobs_command(self, args: list[str]) -> None:
        """Jobs command - Display detailed information from JobManager."""
        # Handle specific job ID
        if args and args[0] not in ["cancel", "kill", "stop"]:
            job_id = self._normalize_job_id(args[0])
            job_details = self.ui_manager.get_job_details(job_id)
            if job_details:
                self._display_job_details(job_id, job_details)
            else:
                self.ui_manager.print_error(f"Job {job_id} not found")
            return

        # Handle job cancellation
        if args and args[0] in ["cancel", "kill", "stop"] and len(args) > 1:
            job_id = self._normalize_job_id(args[1])
            success = await self.ui_manager.cancel_job(job_id)
            if success:
                self.ui_manager.print_success(f"Job {job_id} cancellation requested")
            return

        # Get all jobs from JobManager
        all_jobs = self.ui_manager.job_manager.list_jobs()
        if not all_jobs:
            self.ui_manager.print("[dim]No jobs found[/dim]")
            return

        # Create comprehensive jobs table
        jobs_table = Table(title="Job Status")
        jobs_table.add_column("#", style="yellow", width=3)
        jobs_table.add_column("Job ID", style="cyan", width=10)
        jobs_table.add_column("Status", style="green", width=12)
        jobs_table.add_column("Description", style="white", width=50)
        jobs_table.add_column("Started", style="blue", width=10)
        jobs_table.add_column("Duration", style="yellow", width=10)

        for job in sorted(all_jobs, key=lambda x: x.created_at, reverse=True):
            # Calculate duration
            if job.started_at:
                if job.completed_at:
                    duration = f"{job.completed_at - job.started_at:.1f}s"
                else:
                    import time

                    duration = f"{time.time() - job.started_at:.1f}s"
            else:
                duration = "-"

            # Format status with color
            status_color = {
                "pending": "[yellow]PENDING[/yellow]",
                "running": "[green]RUNNING[/green]",
                "completed": "[blue]COMPLETED[/blue]",
                "failed": "[red]FAILED[/red]",
                "cancelled": "[gray]CANCELLED[/gray]",
            }.get(job.status.value, job.status.value)

            # Format start time (HH:MM:SS only for table)
            start_time = datetime.fromtimestamp(job.started_at).strftime("%H:%M:%S") if job.started_at else "-"

            # Extract numeric ID from job_id (e.g., "job_002" -> "2")
            short_id = job.job_id.replace("job_", "").lstrip("0") or "0"

            jobs_table.add_row(
                short_id,
                job.job_id,
                status_color,
                job.description[:48] + "..." if len(job.description) > 50 else job.description,
                start_time,
                duration,
            )

        self.ui_manager.print(jobs_table)

        # Show summary
        job_counts = self.ui_manager.job_manager.get_job_count()
        running_count = job_counts.get("running", 0)
        total_count = len(all_jobs)

        self.ui_manager.print(f"\n[info]Summary: {running_count} running, {total_count} total jobs[/info]")

        if running_count > 0:
            self.ui_manager.print("[dim]Use '/jobs <job_id>' for details, '/jobs cancel <job_id>' to cancel[/dim]")

    def _normalize_job_id(self, job_id_arg: str) -> str:
        """Convert numeric ID to job_XXX format.

        Examples:
            "2" -> "job_002"
            "10" -> "job_010"
            "job_003" -> "job_003" (unchanged)
        """
        if job_id_arg.isdigit():
            return f"job_{int(job_id_arg):03d}"
        return job_id_arg

    def _display_job_details(self, job_id: str, job_details: dict) -> None:
        """Display detailed information for a specific job."""
        from rich.panel import Panel
        from rich.syntax import Syntax

        # Status color mapping
        status_colors = {
            "running": "green",
            "completed": "blue",
            "failed": "red",
            "cancelled": "yellow",
            "pending": "gray",
        }

        status = job_details.get("status", "unknown")
        status_color = status_colors.get(status, "white")

        # Build the detailed display
        self.ui_manager.print(f"[bold cyan]Job Details: {job_id}[/bold cyan]")
        self.ui_manager.print(f"[{status_color}]● Status: {status.upper()}[/{status_color}]")

        # Basic information
        basic_info = Table.grid(padding=0)
        basic_info.add_column(style="cyan", width=20)
        basic_info.add_column(style="white")

        if job_details.get("tool_name"):
            basic_info.add_row("Tool:", job_details["tool_name"])
        if job_details.get("description"):
            basic_info.add_row("Description:", job_details["description"])
        if job_details.get("purpose"):
            basic_info.add_row("Purpose:", job_details["purpose"])
        if job_details.get("duration"):
            basic_info.add_row("Duration:", job_details["duration"])
        if job_details.get("exit_code") is not None:
            exit_code = job_details["exit_code"]
            exit_color = "green" if exit_code == 0 else "red"
            basic_info.add_row("Exit Code:", f"[{exit_color}]{exit_code}[/{exit_color}]")

        self.ui_manager.print(basic_info)

        # Command display
        if job_details.get("command"):
            self.ui_manager.print("[cyan]Command:[/cyan]")
            # Use Syntax highlighting for better readability
            syntax = Syntax(job_details["command"], "bash", theme="monokai", line_numbers=False)
            self.ui_manager.print(Panel(syntax, border_style="dim"))

        # Error display (if failed)
        if job_details.get("error") and status == "failed":
            self.ui_manager.print("[red]Error:[/red]")
            error_panel = Panel(job_details["error"], border_style="red", title="Error Details")
            self.ui_manager.print(error_panel)

        # Output preview
        if job_details.get("output_preview"):
            output_size = job_details.get("output_size", 0)
            self.ui_manager.print(f"[cyan]Output Preview[/cyan] ({output_size} bytes total):")
            output_panel = Panel(job_details["output_preview"], border_style="dim", title="Output (first 500 chars)")
            self.ui_manager.print(output_panel)

            if output_size > 500:
                self.ui_manager.print("[dim]Use '/logs {job_id}' to see complete output[/dim]")

        # Timing information
        if job_details.get("started_at") or job_details.get("completed_at"):
            self.ui_manager.print("[cyan]Timing:[/cyan]")
            timing_info = Table.grid(padding=0)
            timing_info.add_column(style="cyan", width=20)
            timing_info.add_column(style="white")

            if job_details.get("started_at"):
                timing_info.add_row("Started:", job_details["started_at"])
            if job_details.get("completed_at"):
                timing_info.add_row("Completed:", job_details["completed_at"])

            self.ui_manager.print(timing_info)

    async def _logs_command(self, args: list[str]) -> None:
        """Logs command - Display complete output of job."""
        if not args:
            self.ui_manager.print_error("Usage: /logs <job_id>")
            return

        job_id = self._normalize_job_id(args[0])

        # Get job info from JobManager
        job_info = self.ui_manager.job_manager.get_job_info(job_id)
        if not job_info:
            self.ui_manager.print_error(f"Job {job_id} not found")
            return

        self.ui_manager.print(f"\n[bold cyan]Full Output for Job: {job_id}[/bold cyan]")
        self.ui_manager.print(f"Tool: {job_info.tool_name or 'Unknown'}")
        self.ui_manager.print(f"Command: {job_info.command or 'Unknown'}")
        self.ui_manager.print(f"Status: {job_info.status.value}")

        if job_info.full_output:
            from rich.panel import Panel

            output_panel = Panel(
                job_info.full_output, border_style="dim", title=f"Complete Output ({len(job_info.full_output)} bytes)"
            )
            self.ui_manager.print(output_panel)
        else:
            self.ui_manager.print("[dim]No output available for this job[/dim]")

        # Show error if failed
        if job_info.error and job_info.status.value == "failed":
            error_panel = Panel(job_info.error, border_style="red", title="Error Output")
            self.ui_manager.print(error_panel)

    async def _stop_command(self, args: list[str]) -> None:
        """Stop command."""
        if not args:
            self.ui_manager.print_error("Usage: /stop <job_id>")
            return

        job_id = self._normalize_job_id(args[0])
        success = await self.ui_manager.cancel_job(job_id)

        if success:
            self.ui_manager.print(f"Job [cyan]{job_id}[/cyan] stopped")
        else:
            self.ui_manager.print_error(f"Could not stop job {job_id}")

    async def _sliver_command(self, args: list[str]) -> None:
        """Sliver command."""
        if not self.c2_connector:
            self.ui_manager.print("[red]Sliver C2 is not configured[/red]")
            return

        # Lazy import to avoid circular dependencies
        from .sliver import SliverCommand

        sliver_cmd = SliverCommand(self.c2_connector, ui_manager=self.ui_manager)
        result = await sliver_cmd.execute(args)

        # If shell command returned an InteractiveShell, set it in command dispatcher
        if result and hasattr(result, "execute") and hasattr(result, "close"):
            # This is an InteractiveShell instance
            if self.command_dispatcher:
                self.command_dispatcher.set_current_shell(result)

    async def _clear_command(self, args: list[str]) -> None:
        """Clear command."""
        # Clear console
        self.ui_manager.console.clear()
        self.ui_manager.print("Console cleared")

    async def _history_command(self, args: list[str]) -> None:
        """History command."""
        if self.current_session and self.current_session.command_history:
            table = Table(title="Command History", show_header=True, header_style="bold")
            table.add_column("#", style="dim", width=6)
            table.add_column("Command", style="cyan")

            # Show last 20 commands
            history = self.current_session.command_history[-20:]
            for i, cmd in enumerate(history, 1):
                table.add_row(str(i), cmd)

            self.ui_manager.print(table)
        else:
            self.ui_manager.print("[dim]No command history available[/dim]")

    async def _config_command(self, args: list[str]) -> None:
        """Config command."""
        # Import config module
        try:
            from wish_core.config import get_config

            config = get_config()

            # Create config table
            config_table = Table(title="wish Configuration", show_header=True, header_style="bold")
            config_table.add_column("Setting", style="cyan", width=30)
            config_table.add_column("Value", style="white")

            # Basic settings
            config_table.add_row("Config Path", str(config.config_path))

            # LLM settings
            if hasattr(config, "llm"):
                config_table.add_row("LLM Provider", getattr(config.llm, "provider", "openai"))
                config_table.add_row("LLM Model", getattr(config.llm, "model", "gpt-4o"))
                config_table.add_row("Max Tokens", str(getattr(config.llm, "max_tokens", 8000)))
                config_table.add_row("Temperature", str(getattr(config.llm, "temperature", 0.1)))
                api_key = getattr(config.llm, "api_key", None)
                if api_key:
                    config_table.add_row("API Key", f"***{api_key[-4:]}" if len(api_key) > 4 else "****")
                else:
                    config_table.add_row("API Key", "[red]Not configured[/red]")

            # Tool settings
            if hasattr(config, "tools"):
                config_table.add_row("Default Tool Timeout", f"{getattr(config.tools, 'default_timeout', 300)}s")
                config_table.add_row("Max Concurrent Jobs", str(getattr(config.tools, "max_concurrent_jobs", 5)))

            # C2 settings
            if hasattr(config, "c2") and hasattr(config.c2, "sliver"):
                sliver_config = getattr(config.c2.sliver, "config_path", None)
                if sliver_config:
                    config_table.add_row("Sliver Config", str(sliver_config))
                else:
                    config_table.add_row("Sliver Config", "[dim]Not configured[/dim]")

            self.ui_manager.print(config_table)

            # Show config file location hint
            self.ui_manager.print("\n[dim]Configuration file: ~/.wish/config.toml[/dim]")
            self.ui_manager.print("[dim]Environment variables override config file settings[/dim]")

        except Exception as e:
            logger.error(f"Failed to display config: {e}")
            self.ui_manager.print_error(f"Could not load configuration: {e}")

    async def shutdown(self) -> None:
        """Handler shutdown processing."""
        logger.info("Slash command handler shutdown complete")
