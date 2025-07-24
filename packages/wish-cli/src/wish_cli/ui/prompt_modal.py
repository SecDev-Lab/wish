# wish_cli/ui/prompt_modal.py
"""
Modal dialogs for wish using Rich panels and prompt_toolkit.
Based on modern style for consistency.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any

from prompt_toolkit import prompt
from rich.console import Console
from rich.panel import Panel

from wish_cli.ui.colors import BORDER_PRIMARY, BORDER_SECONDARY, COMMAND_COLOR

logger = logging.getLogger(__name__)


class ApprovalChoice(Enum):
    """Approval dialog choices."""

    YES = "yes"
    EDIT = "edit"
    REVISE = "revise"
    COPY = "copy"
    CANCEL = "cancel"


class PromptModal:
    """Base class for modal dialogs using Rich + prompt_toolkit."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def _display_plan(self, plan: Any) -> None:
        """Display execution plan in Rich format."""
        # Plan description
        if hasattr(plan, "description"):
            self.console.print("\n[bold cyan]Plan Description:[/bold cyan]")
            self.console.print(f"  {plan.description}")

        # Commands to execute
        if hasattr(plan, "steps"):
            self.console.print("\n[bold cyan]Commands to Execute:[/bold cyan]")
            for i, step in enumerate(plan.steps, 1):
                if hasattr(step, "command"):
                    self.console.print(f"\n  [{COMMAND_COLOR}]{i}. {step.command}[/{COMMAND_COLOR}]")
                    if hasattr(step, "purpose"):
                        self.console.print(f"     [dim]{step.purpose}[/dim]")

        self.console.print()


class ApprovalModal(PromptModal):
    """Plan approval modal dialog."""

    async def show(self, plan: Any) -> ApprovalChoice:
        """Show approval dialog and return user choice."""
        # Display the plan
        self._display_plan(plan)

        # Create options panel
        options_text = """[bold yellow]Run this script?[/bold yellow]

[green]1.[/green] ✅ Yes (Lets go!)
[yellow]2.[/yellow] 📝 Edit
[cyan]3.[/cyan] 🔁 Revise
[blue]4.[/blue] 📋 Copy
[red]5.[/red] ❌ Cancel

Select an option (1-5) or press Enter for the highlighted option:"""

        self.console.print(Panel(options_text, style=BORDER_PRIMARY, padding=(1, 2)))

        # Get user input with prompt_toolkit
        try:
            while True:
                user_input = await asyncio.to_thread(prompt, "> ", default="1")
                user_input = user_input.strip().lower()

                if user_input in ["1", "y", "yes", ""]:
                    return ApprovalChoice.YES
                elif user_input in ["2", "e", "edit"]:
                    return ApprovalChoice.EDIT
                elif user_input in ["3", "r", "revise"]:
                    return ApprovalChoice.REVISE
                elif user_input in ["4", "c", "copy"]:
                    return ApprovalChoice.COPY
                elif user_input in ["5", "n", "no", "cancel"]:
                    return ApprovalChoice.CANCEL
                else:
                    self.console.print("[warning]Invalid choice. Please select 1-5.[/warning]")

        except (KeyboardInterrupt, EOFError):
            return ApprovalChoice.CANCEL


class EditModal(PromptModal):
    """Plan edit modal dialog."""

    async def show(self, plan: Any) -> str | None:
        """Show edit dialog and return edited content."""
        # Build editable content
        lines = []

        if hasattr(plan, "description"):
            lines.append(f"# Plan: {plan.description}")
            lines.append("")

        if hasattr(plan, "steps"):
            for i, step in enumerate(plan.steps, 1):
                if hasattr(step, "purpose"):
                    lines.append(f"# Step {i}: {step.purpose}")
                if hasattr(step, "command"):
                    lines.append(step.command)
                lines.append("")

        # Display instructions
        self.console.print(
            Panel(
                "[bold cyan]Edit Plan[/bold cyan]\n\n"
                "Edit the commands below. Lines starting with # are comments.\n"
                "Press Ctrl+D when done, or Ctrl+C to cancel.",
                style=BORDER_SECONDARY,
                padding=(1, 2),
            )
        )

        try:
            # Multi-line input
            self.console.print("\n[dim]Enter/paste your content. Press Ctrl+D when done:[/dim]\n")

            edited_lines = []
            while True:
                try:
                    line = await asyncio.to_thread(input)
                    edited_lines.append(line)
                except EOFError:
                    break

            return "\n".join(edited_lines) if edited_lines else None

        except KeyboardInterrupt:
            self.console.print("\n[info]Edit cancelled[/info]")
            return None


class ReviseModal(PromptModal):
    """Plan revision request modal."""

    async def show(self, plan: Any) -> str | None:
        """Show revision dialog and return revision request."""
        # Display current plan
        self._display_plan(plan)

        # Display instructions
        self.console.print(
            Panel(
                "[bold cyan]Request Plan Revision[/bold cyan]\n\n"
                "Describe how you'd like the plan to be revised.\n"
                "The AI will generate a new plan based on your feedback.",
                style=BORDER_SECONDARY,
                padding=(1, 2),
            )
        )

        try:
            revision_request = await asyncio.to_thread(
                prompt, "\nRevision request (or press Enter for general improvement): "
            )

            return revision_request.strip() if revision_request.strip() else "Please improve this plan"

        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[info]Revision cancelled[/info]")
            return None


class ConfirmModal(PromptModal):
    """Simple confirmation modal."""

    async def show(self, message: str, title: str = "Confirm") -> bool:
        """Show confirmation dialog."""
        self.console.print(
            Panel(f"{message}\n\n[bold]Continue? (y/N):[/bold]", title=title, style=BORDER_PRIMARY, padding=(1, 2))
        )

        try:
            response = await asyncio.to_thread(prompt, "> ", default="n")
            return response.strip().lower() in ["y", "yes"]

        except (KeyboardInterrupt, EOFError):
            return False
