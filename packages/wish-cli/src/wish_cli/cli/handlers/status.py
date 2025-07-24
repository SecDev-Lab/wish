"""Status command handler for wish CLI."""

import logging
from typing import Any

from wish_core.state.manager import StateManager

logger = logging.getLogger(__name__)


class StatusCommandHandler:
    """Status command handler for displaying engagement status."""

    def __init__(self, state_manager: StateManager, input_app: Any | None = None):
        self.state_manager = state_manager
        self.input_app = input_app

    def set_input_app(self, input_app: Any) -> None:
        """Set the input app for output operations."""
        self.input_app = input_app

    async def handle_status(self) -> None:
        """Handle status command."""
        if not self.input_app:
            return

        try:
            current_state = await self.state_manager.get_current_state()

            targets_count = len(current_state.targets) if current_state.targets else 0
            hosts_count = len(current_state.hosts) if current_state.hosts else 0
            findings_count = len(current_state.findings) if current_state.findings else 0

            # Build status information
            status_lines = [
                "╭─────────────────────────────── Engagement Status ───────────────────────────────╮",
                "│ 🎯 Engagement Status                                                         │",
                f"│ ├── 📍 Targets: {targets_count}                                                            │",
                f"│ ├── 🖥️ Hosts: {hosts_count}                                                               │",
                f"│ ├── 🔍 Findings: {findings_count}                                                           │",
                "│ └── 📊 Collected Data                                                        │",
                "│     └── Recent command results                                               │",
            ]

            # Host information details
            if hosts_count > 0:
                status_lines.append("│                                                                              │")
                status_lines.append("│ 🖥️ Discovered Hosts:                                                        │")
                for _host_id, host in list(current_state.hosts.items())[:3]:
                    host_line = f"│   ├── {host.ip_address} ({host.status})"
                    if host.services:
                        host_line += f" - {len(host.services)} services"
                    # Pad to 80 characters
                    host_line = host_line.ljust(79) + "│"
                    status_lines.append(host_line)

            # Discovery information details
            if findings_count > 0:
                status_lines.append("│                                                                              │")
                status_lines.append("│ 🔍 Recent Findings:                                                         │")
                for _finding_id, finding in list(current_state.findings.items())[:2]:
                    finding_line = f"│   ├── {finding.title}"
                    if finding.severity:
                        finding_line += f" ({finding.severity})"
                    # Pad to 80 characters
                    finding_line = finding_line.ljust(79) + "│"
                    status_lines.append(finding_line)

            status_lines.append("╰──────────────────────────────────────────────────────────────────────────────╯")

            # Output
            for line in status_lines:
                self.input_app.write_output(line)

        except Exception as e:
            logger.error(f"Error showing status: {e}")
            self.input_app.write_output(f"[error]Error retrieving status: {e}[/error]")
