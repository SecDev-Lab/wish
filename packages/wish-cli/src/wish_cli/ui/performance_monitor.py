# wish_cli/ui/performance_monitor.py
"""
Performance monitoring and progress display for wish.
Based on modern performance tracking approach.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from wish_cli.ui.colors import BORDER_SECONDARY

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    command: str
    start_time: float
    end_time: float | None = None
    tokens_used: int = 0
    tool_calls: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def duration(self) -> float:
        """Calculate duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    @property
    def status(self) -> str:
        """Get status of the command."""
        if self.error:
            return "failed"
        elif self.end_time:
            return "completed"
        else:
            return "running"


class PerformanceMonitor:
    """Monitor and display performance metrics."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.metrics: dict[str, PerformanceMetrics] = {}
        self.active_progress: Progress | None = None
        self._current_task_id: int | None = None

    def start_command(self, command_id: str, command: str) -> None:
        """Start tracking a command."""
        self.metrics[command_id] = PerformanceMetrics(command=command, start_time=time.time())
        logger.debug(f"Started tracking command {command_id}: {command}")

    def end_command(self, command_id: str, error: str | None = None) -> None:
        """End tracking a command."""
        if command_id in self.metrics:
            self.metrics[command_id].end_time = time.time()
            if error:
                self.metrics[command_id].error = error
            logger.debug(f"Ended tracking command {command_id}, duration: {self.metrics[command_id].duration:.2f}s")

    def add_tool_call(self, command_id: str, tool_name: str) -> None:
        """Add a tool call to a command's metrics."""
        if command_id in self.metrics:
            self.metrics[command_id].tool_calls.append(tool_name)

    def update_tokens(self, command_id: str, tokens: int) -> None:
        """Update token count for a command."""
        if command_id in self.metrics:
            self.metrics[command_id].tokens_used += tokens

    def show_progress(self, message: str, total: int | None = None) -> Progress:
        """Show a progress bar."""
        if self.active_progress:
            self.active_progress.stop()

        self.active_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            console=self.console,
            transient=True,
        )

        self.active_progress.start()

        if total:
            task = self.active_progress.add_task(message, total=total)
        else:
            task = self.active_progress.add_task(message)

        self._current_task_id = task  # Store for updates

        return self.active_progress

    def update_progress(self, completed: int) -> None:
        """Update current progress."""
        if self.active_progress and hasattr(self, "_current_task_id") and self._current_task_id is not None:
            self.active_progress.update(self._current_task_id, completed=completed)

    def stop_progress(self) -> None:
        """Stop current progress display."""
        if self.active_progress:
            self.active_progress.stop()
            self.active_progress = None

    def display_metrics(self, last_n: int = 10) -> None:
        """Display performance metrics table."""
        if not self.metrics:
            self.console.print("[dim]No performance metrics available[/dim]")
            return

        # Create table
        table = Table(title="Performance Metrics", show_header=True, header_style="bold")
        table.add_column("Command", style="cyan", max_width=40)
        table.add_column("Status", style="yellow")
        table.add_column("Duration", style="white")
        table.add_column("Tools", style="magenta")
        table.add_column("Tokens", style="green")

        # Get last N metrics
        recent_metrics = list(self.metrics.values())[-last_n:]

        for metric in recent_metrics:
            # Format command (truncate if needed)
            cmd = metric.command
            if len(cmd) > 40:
                cmd = cmd[:37] + "..."

            # Format status with color
            if metric.status == "completed":
                status = "[green]✓ Completed[/green]"
            elif metric.status == "failed":
                status = "[red]✗ Failed[/red]"
            else:
                status = "[yellow]⟳ Running[/yellow]"

            # Format duration
            duration = f"{metric.duration:.2f}s"

            # Format tools
            tools = ", ".join(metric.tool_calls[:3])
            if len(metric.tool_calls) > 3:
                tools += f" (+{len(metric.tool_calls) - 3})"

            # Format tokens
            tokens = str(metric.tokens_used) if metric.tokens_used > 0 else "-"

            table.add_row(cmd, status, duration, tools, tokens)

        self.console.print(table)

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics."""
        if not self.metrics:
            return {}

        completed = [m for m in self.metrics.values() if m.status == "completed"]
        failed = [m for m in self.metrics.values() if m.status == "failed"]

        total_duration = sum(m.duration for m in completed)
        avg_duration = total_duration / len(completed) if completed else 0

        total_tokens = sum(m.tokens_used for m in self.metrics.values())
        total_tools = sum(len(m.tool_calls) for m in self.metrics.values())

        return {
            "total_commands": len(self.metrics),
            "completed": len(completed),
            "failed": len(failed),
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "total_tokens": total_tokens,
            "total_tool_calls": total_tools,
            "success_rate": len(completed) / len(self.metrics) * 100 if self.metrics else 0,
        }

    def display_summary(self) -> None:
        """Display performance summary."""
        stats = self.get_summary_stats()

        if not stats:
            self.console.print("[dim]No performance data available[/dim]")
            return

        # Build summary content
        summary_text = Text()
        summary_text.append("Session Performance Summary\n\n", style="bold")

        summary_text.append("Total Commands: ", style="cyan")
        summary_text.append(f"{stats['total_commands']}\n")

        summary_text.append("Success Rate: ", style="cyan")
        summary_text.append(f"{stats['success_rate']:.1f}%\n")

        summary_text.append("Total Duration: ", style="cyan")
        summary_text.append(f"{stats['total_duration']:.2f}s\n")

        summary_text.append("Average Duration: ", style="cyan")
        summary_text.append(f"{stats['average_duration']:.2f}s\n")

        if stats["total_tokens"] > 0:
            summary_text.append("Tokens Used: ", style="cyan")
            summary_text.append(f"{stats['total_tokens']:,}\n")

        if stats["total_tool_calls"] > 0:
            summary_text.append("Tool Calls: ", style="cyan")
            summary_text.append(f"{stats['total_tool_calls']}\n")

        # Display in panel
        self.console.print(Panel(summary_text, title="Performance Summary", style=BORDER_SECONDARY, padding=(1, 2)))
