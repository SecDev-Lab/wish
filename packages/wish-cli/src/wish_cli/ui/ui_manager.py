"""Simplified UI Manager using only Rich Console for output."""

import logging
import os
from io import StringIO
from typing import Any

from rich.console import Console
from rich.theme import Theme

from wish_cli.core.job_manager import JobInfo, JobManager, JobStatus
from wish_cli.ui.colors import (
    BORDER_PRIMARY,
    COMMAND_COLOR,
    STEP_COLOR,
    TEXT_ERROR,
    TEXT_INFO,
    TEXT_SUCCESS,
    TEXT_WARNING,
    TOOL_COLOR,
)

logger = logging.getLogger(__name__)


class WishUIManager:
    """Simplified UI manager - Rich Console only for output."""

    def __init__(self) -> None:
        # Rich Console setup - modern style colors
        self.theme = Theme(
            {
                "info": TEXT_INFO,
                "warning": TEXT_WARNING,
                "error": TEXT_ERROR,
                "success": TEXT_SUCCESS,
                "wish.step": STEP_COLOR,
                "wish.tool": TOOL_COLOR,
                "wish.command": COMMAND_COLOR,
            }
        )

        # Console initialization
        self.console = Console(theme=self.theme, force_terminal=True, width=None, height=None)

        # For WishApp integration
        self._output_callback = None
        self._input_app = None  # Reference to MinimalInputApp

        # For approval UI
        self._enable_approval_mode = False
        self._pending_approval_callback = None

        # Job management
        self.job_manager = JobManager(max_concurrent_jobs=10)
        self._running_jobs: dict[str, dict[str, str]] = {}  # Legacy support

        # Reference to CommandDispatcher (set later)
        self._command_dispatcher = None

    def set_command_dispatcher(self, dispatcher: Any) -> None:
        """Set reference to CommandDispatcher."""
        self._command_dispatcher = dispatcher

    async def initialize(self) -> None:
        """UI initialization."""
        logger.info("Initializing simplified UI manager...")
        logger.info("UI manager initialized successfully")

    async def shutdown(self) -> None:
        """UI shutdown processing."""
        logger.info("Shutting down UI manager...")
        await self.job_manager.shutdown()
        logger.info("UI manager shutdown complete")

    def set_output_callback(self, callback: Any) -> None:
        """Set output callback from WishApp."""
        self._output_callback = callback
        logger.info(f"Output callback set: {callback is not None}")

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Rich print - output to WishApp if available."""
        if self._output_callback:
            # Render Rich objects appropriately
            from rich.panel import Panel
            from rich.table import Table
            from rich.tree import Tree

            # For single Rich object
            if len(args) == 1 and isinstance(args[0], Table | Panel | Tree):
                # Render Rich object using StringIO
                string_io = StringIO()
                # Match Textual app width (if available)
                width = 80  # Default width
                try:
                    # Get actual width if Textual app is available
                    import os

                    terminal_width = os.get_terminal_size().columns
                    width = min(max(terminal_width - 4, 40), 120)  # Limit to appropriate range
                except Exception as e:
                    logger.debug(f"Could not get terminal size: {e}")
                temp_console = Console(file=string_io, force_terminal=False, width=width)
                temp_console.print(args[0])
                rendered_content = string_io.getvalue()
                # Remove trailing newlines (prevent flicker)
                rendered_content = rendered_content.rstrip()
                if rendered_content:
                    self._output_callback(rendered_content)
            else:
                # For regular text
                message = " ".join(str(arg) for arg in args)
                if message:  # Skip empty messages
                    self._output_callback(message)
        else:
            # Fallback: Use regular print()
            logger.debug("Output callback not set - using print() fallback")

            # Render Rich objects appropriately
            from rich.panel import Panel
            from rich.table import Table
            from rich.text import Text
            from rich.tree import Tree

            # For single Rich object - render with StringIO then output
            if len(args) == 1 and isinstance(args[0], Table | Panel | Tree):
                # Convert Rich object to plain text using StringIO
                string_io = StringIO()
                # Adjust to terminal width
                width = 80  # Default width
                try:
                    import os

                    terminal_width = os.get_terminal_size().columns
                    width = min(max(terminal_width - 4, 40), 120)  # Limit to appropriate range
                except Exception as e:
                    logger.debug(f"Could not get terminal size: {e}")
                temp_console = Console(file=string_io, force_terminal=False, width=width)
                temp_console.print(args[0])
                rendered_content = string_io.getvalue()
                print(rendered_content)
            else:
                # For regular text
                plain_text = []
                for arg in args:
                    if isinstance(arg, str):
                        # Remove Rich markup
                        text_obj = Text.from_markup(arg)
                        plain_text.append(text_obj.plain)
                    else:
                        plain_text.append(str(arg))
                print(" ".join(plain_text))

    def print_info(self, message: str) -> None:
        """Display information."""
        self.print(f"[info]{message}[/info]")

    def print_error(self, message: str) -> None:
        """Display error."""
        self.print(f"[error]Error: {message}[/error]")

    def print_success(self, message: str) -> None:
        """Display success."""
        self.print(f"[success]{message}[/success]")

    def update_status(self, mode: str, targets: int = 0, jobs: int = 0) -> None:
        """Update status."""
        # For knowledge base import progress, we display directly
        if "Importing HackTricks" in mode:
            self.console.print(f"[info]{mode}[/info]")

    def show_knowledge_progress(self, stage: str, progress: float) -> None:
        """Display knowledge base import progress."""
        from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

        # Create or update progress display
        if not hasattr(self, "_kb_progress"):
            self._kb_progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                console=self.console,
                transient=True,
            )
            self._kb_progress.start()
            self._kb_task = self._kb_progress.add_task(f"Importing HackTricks ({stage})", total=100)

        # Update progress
        self._kb_progress.update(self._kb_task, description=f"Importing HackTricks ({stage})", completed=progress)

        # Clean up on completion
        if progress >= 100:
            self._kb_progress.stop()
            delattr(self, "_kb_progress")
            delattr(self, "_kb_task")

    def get_running_jobs(self) -> list[str]:
        """Get running jobs."""
        return self.job_manager.get_running_jobs()

    async def get_user_input(self) -> str:
        """Get user input - delegate to Textual App."""
        # This part is implemented in the new Textual App
        return "exit"

    # Missing methods required by command_dispatcher.py
    def print_plan(self, plan: Any) -> None:
        """Display plan - modern style."""
        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text

        # Build plan content
        content_parts = []

        if hasattr(plan, "description"):
            desc_text = Text()
            desc_text.append("Description: ", style="bold cyan")
            desc_text.append(plan.description)
            content_parts.append(desc_text)
            content_parts.append(Text(""))  # Empty line

        if hasattr(plan, "steps"):
            content_parts.append(Text("Commands to execute:", style="bold cyan"))
            for i, step in enumerate(plan.steps, 1):
                if hasattr(step, "command"):
                    cmd_text = Text()
                    cmd_text.append(f"  {i}. ", style="dim")
                    cmd_text.append(step.command, style=COMMAND_COLOR)
                    content_parts.append(cmd_text)

                    if hasattr(step, "purpose"):
                        purpose_text = Text(f"     {step.purpose}", style="dim")
                        content_parts.append(purpose_text)

        # Display in panel
        if self._output_callback:
            # Render to string for output callback
            from io import StringIO

            string_io = StringIO()
            temp_console = Console(file=string_io, force_terminal=False, width=80)
            temp_console.print(
                Panel(Group(*content_parts), title="Execution Plan", style=BORDER_PRIMARY, padding=(1, 2))
            )
            self._output_callback(string_io.getvalue().rstrip())
        else:
            # Direct print using console
            self.console.print(
                Panel(Group(*content_parts), title="Execution Plan", style=BORDER_PRIMARY, padding=(1, 2))
            )

    async def request_plan_approval(self, plan: Any) -> bool:
        """Plan approval request - arrow key selection UI."""
        # Note: plan is already displayed by command_dispatcher

        try:
            # Try to use arrow key selection UI
            from prompt_toolkit.application import Application
            from prompt_toolkit.key_binding import KeyBindings
            from prompt_toolkit.layout import Layout
            from prompt_toolkit.layout.containers import Window
            from prompt_toolkit.layout.controls import FormattedTextControl

            # Current selection index
            selected_index = 0
            choices = [
                ("yes", "✅ Yes (run it!)"),
                ("no", "❌ No (cancel)"),
                ("edit", "📝 Edit"),
                ("revise", "🔁 Revise"),
            ]

            def get_formatted_text():
                """Get formatted text with current selection highlighted."""
                lines = []
                lines.append(("", "\n"))
                lines.append(("bold", "Run this script?"))
                lines.append(("", "\n"))
                lines.append(("class:dim", "Use ↑↓ arrows to select, Enter to confirm, ESC to cancel"))
                lines.append(("", "\n\n"))

                for i, (_, label) in enumerate(choices):
                    if i == selected_index:
                        lines.append(("reverse", f" → {label} "))
                    else:
                        lines.append(("", f"   {label}"))
                    lines.append(("", "\n"))

                return lines

            # Create control
            control = FormattedTextControl(get_formatted_text)
            window = Window(control, height=len(choices) + 4)

            # Key bindings
            kb = KeyBindings()

            @kb.add("up")
            def _(event):
                nonlocal selected_index
                selected_index = (selected_index - 1) % len(choices)
                control.text = get_formatted_text()

            @kb.add("down")
            def _(event):
                nonlocal selected_index
                selected_index = (selected_index + 1) % len(choices)
                control.text = get_formatted_text()

            @kb.add("enter")
            def _(event):
                event.app.exit(result=choices[selected_index][0])

            @kb.add("c-c")
            @kb.add("escape")
            def _(event):
                event.app.exit(result="no")

            # Create style
            from prompt_toolkit.styles import Style

            style = Style.from_dict(
                {
                    "dim": "#888888",
                    "bold": "bold",
                    "reverse": "reverse",
                }
            )

            # Create and run application
            app = Application(
                layout=Layout(window),
                key_bindings=kb,
                style=style,
                mouse_support=False,
                full_screen=False,
            )

            result = await app.run_async()

            # Clear the selection UI by printing empty lines
            self.print("\033[F" * (len(choices) + 4))  # Move cursor up
            self.print(" " * 60 + "\n" * (len(choices) + 3))  # Clear lines
            self.print("\033[F" * (len(choices) + 4))  # Move cursor back up

            # Process result
            if result == "yes":
                self.print("[green]→ Running plan...[/green]\n")
                return True
            elif result == "no":
                self.print("[red]→ Plan cancelled[/red]\n")
                return False
            elif result == "edit":
                self.print("[yellow]→ Edit mode not yet implemented[/yellow]\n")
                return False
            elif result == "revise":
                self.print("[yellow]→ Revise mode not yet implemented[/yellow]\n")
                return False

        except Exception as e:
            # Fallback to simple input if arrow key UI fails
            logger.warning(f"Arrow key UI failed, falling back to simple input: {e}")
            return await self._simple_approval_prompt()

    async def _simple_approval_prompt(self) -> bool:
        """Simple text-based approval prompt as fallback."""

        import asyncio

        try:
            self.print("\n[bold yellow]Run this script?[/bold yellow]")
            self.print("[green]y[/green] = Yes  [red]n[/red] = No  [yellow]e[/yellow] = Edit  [blue]r[/blue] = Revise")

            while True:
                try:
                    choice = await asyncio.to_thread(input, "> ")
                    # Echo the choice for visibility
                    self.print(f"[dim]> {choice}[/dim]")
                except EOFError:
                    choice = "n"

                choice = choice.strip().lower()

                if choice in ["y", "yes"]:
                    self.print("[green]→ Running plan...[/green]\n")
                    return True
                elif choice in ["n", "no"]:
                    self.print("[red]→ Plan cancelled[/red]\n")
                    return False
                elif choice in ["e", "edit"]:
                    self.print("[yellow]→ Edit mode not yet implemented[/yellow]")
                    continue
                elif choice in ["r", "revise"]:
                    self.print("[yellow]→ Revise mode not yet implemented[/yellow]")
                    continue
                else:
                    self.print("[warning]Invalid choice. Please enter y/n/e/r[/warning]")

        except (KeyboardInterrupt, EOFError):
            self.print("\n[red]→ Plan cancelled[/red]\n")
            return False

        # Original complex logic below - will be replaced with prompt_toolkit modals
        modal_available = self._input_app and hasattr(self._input_app, "set_approval_mode")

        if not modal_available:
            # Fallback: Display text-based approval UI
            self.print("\n[cyan]◆  Run this script?[/cyan]")
            self.print("│  ● ✅ Yes (Lets go!)")
            self.print("│  ○ 📝 Edit")
            self.print("│  ○ 🔁 Revise")
            self.print("│  ○ 📋 Copy")
            self.print("│  ○ ❌ Cancel")
            self.print("└")
            self.print("")
            self.print("[info]Select an option (1-5) or press Enter for the highlighted option:[/info]")
            self.print("")

        # Check if MinimalInputApp is set

        if self._output_callback:
            # Get MinimalInputApp instance
            # In current implementation, HybridUIManager manages MinimalInputApp
            # Need access to that instance

            # Wait for approval using callback implementation
            import asyncio

            approval_event = asyncio.Event()
            approval_result = {"response": None}

            def approval_callback(response: str):
                approval_result["response"] = response
                approval_event.set()

            # Set approval mode in MinimalInputApp
            if self._input_app:
                logger.info(f"MinimalInputApp available: {self._input_app}")
                if hasattr(self._input_app, "set_approval_mode"):
                    logger.info("Calling set_approval_mode on MinimalInputApp")
                    # Pass empty plan for now as we don't have access to it here
                    self._input_app.set_approval_mode(True, approval_callback, {})
                else:
                    logger.error("MinimalInputApp does not have set_approval_mode method")
                    # Fallback
                    self.print("[yellow]→ Auto-approving (method not available)...[/yellow]\n")
                    return True
            else:
                logger.warning(f"MinimalInputApp not available: _input_app={self._input_app}")
                # Fallback
                self.print("[yellow]→ Auto-approving (UI not available)...[/yellow]\n")
                return True

            # Wait for approval with timeout
            try:
                await asyncio.wait_for(approval_event.wait(), timeout=60.0)

                if approval_result["response"] == "yes":
                    self.print("\n[success]Plan approved! Executing...[/success]")
                    return True
                elif approval_result["response"] == "cancel":
                    self.print("\n[info]Plan cancelled by user[/info]")
                    return False
                elif approval_result["response"] == "copy":
                    # Copy feature: Copy commands to clipboard
                    # We don't have access to plan here, so pass empty dict
                    success = self._copy_plan_to_clipboard({})
                    if success:
                        self.print("\n[success]Commands copied to clipboard![/success]")
                    else:
                        self.print("\n[warning]Failed to copy to clipboard[/warning]")
                    return False  # Do not execute plan
                elif approval_result["response"] == "edit":
                    # Edit feature: Edit plan
                    self.print("\n[info]Opening plan editor...[/info]")
                    # We don't have access to plan here, so pass empty dict
                    edited_plan = await self._edit_plan({})
                    if edited_plan:
                        # Re-enter approval process with edited plan
                        self.print("\n[info]Plan edited successfully. Review the changes:[/info]")
                        self.print_plan(edited_plan)
                        return await self.request_plan_approval(edited_plan)
                    else:
                        self.print("\n[info]Plan editing cancelled[/info]")
                        return False
                elif approval_result["response"] == "revise":
                    # Revise feature: AI-based plan revision
                    self.print("\n[info]Requesting plan revision from AI...[/info]")
                    # We don't have access to plan here, so pass empty dict
                    revised_plan = await self._revise_plan({})
                    if revised_plan:
                        # Re-enter approval process with corrected plan
                        self.print("\n[info]Plan revised successfully. Review the new plan:[/info]")
                        self.print_plan(revised_plan)
                        return await self.request_plan_approval(revised_plan)
                    else:
                        self.print("\n[info]Plan revision cancelled or failed[/info]")
                        return False
                else:
                    # Unknown response
                    self.print(f"\n[warning]Unknown response: {approval_result['response']} - cancelling[/warning]")
                    return False

            except TimeoutError:
                self.print("\n[warning]Approval timeout - cancelling plan[/warning]")
                return False
            finally:
                # Disable approval mode
                if self._input_app and hasattr(self._input_app, "set_approval_mode"):
                    self._input_app.set_approval_mode(False)
                self._enable_approval_mode = False
                self._pending_approval_callback = None
        else:
            # Fallback: Auto-approve
            self.print("[yellow]→ Auto-approving (no UI callback available)...[/yellow]\n")
            return True

        # TODO: Implement proper interactive approval when MinimalInputApp supports it
        # The code below doesn't work because input() is blocked by Textual
        """
        # Define options
        options = [
            ("1", "✅ Yes (Lets go!)", True),
            ("2", "📝 Edit", "edit"),
            ("3", "🔁 Revise", "revise"),
            ("4", "📋 Copy", "copy"),
            ("5", "❌ Cancel", False),
        ]

        current_selection = 0

        while True:
            # Clear previous options display (simple approach)
            self.print("\n◆  Run this script?")

            # Display options with selection indicator
            for i, (key, label, _) in enumerate(options):
                indicator = "●" if i == current_selection else "○"
                self.print(f"│  {indicator} {label}")
            self.print("└")

            # Simple input prompt
            self.print("\n[info]Select an option (1-5) or press Enter for the highlighted option:[/info]")

            # Get user input - for now using simple approach
            # In a real terminal app, we'd capture key events
            try:
                # Create a simple async input function
                async def ainput(prompt=""):
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, input, prompt)

                user_input = await asyncio.wait_for(ainput("> "), timeout=60.0)
                user_input = user_input.strip().lower()

                # Handle input
                if user_input == "":
                    # Enter pressed - use current selection
                    _, _, action = options[current_selection]
                    break
                elif user_input in ["1", "y", "yes"]:
                    action = True
                    break
                elif user_input in ["2", "e", "edit"]:
                    self.print("[warning]Edit functionality not yet implemented[/warning]")
                    continue
                elif user_input in ["3", "r", "revise"]:
                    self.print("[warning]Revise functionality not yet implemented[/warning]")
                    continue
                elif user_input in ["4", "c", "copy"]:
                    # Copy commands to clipboard
                    if hasattr(plan, "steps"):
                        commands = []
                        for step in plan.steps:
                            if hasattr(step, "command"):
                                commands.append(step.command)
                        if commands:
                            import pyperclip  # type: ignore[import-not-found]

                            try:
                                pyperclip.copy("\\n".join(commands))
                                self.print("[success]Commands copied to clipboard![/success]")
                            except Exception:
                                self.print("[warning]Could not copy to clipboard[/warning]")
                    continue
                elif user_input in ["5", "n", "no", "cancel"]:
                    action = False
                    break
                else:
                    self.print("[warning]Invalid selection. Please choose 1-5.[/warning]")

            except asyncio.TimeoutError:
                self.print("\n[warning]Approval timeout - cancelling plan[/warning]")
                return False
            except KeyboardInterrupt:
                self.print("\n[info]Plan cancelled by user[/info]")
                return False
            except Exception as e:
                logger.error(f"Error in plan approval: {e}")
                self.print("[error]Error during approval process - auto-approving[/error]")
                return True

        if action is True:
            self.print("\n[success]Plan approved! Executing...[/success]")
            return True
        elif action is False:
            self.print("\n[info]Plan cancelled by user[/info]")
            return False
        else:
            # For edit/revise - not implemented yet
            self.print(f"\n[warning]{action.capitalize()} not yet implemented - cancelling[/warning]")
            return False
        """

    def print_step_execution(self, tool_name: str, job_id: str) -> None:
        """Step execution start notification."""
        # Add job to tracking
        from datetime import datetime

        self._running_jobs[job_id] = {
            "tool_name": tool_name,
            "status": "running",
            "started_at": datetime.now().strftime("%H:%M:%S"),
        }
        self.print(f"[info]Executing {tool_name} (job: {job_id})[/info]")

    async def start_background_job(
        self,
        job_id: str,
        description: str,
        job_coroutine: Any,
        command: str | None = None,
        tool_name: str | None = None,
        step_info: dict[str, Any] | None = None,
    ) -> None:
        """Start background job - true asynchronous execution."""
        self.print(f"[info]Starting background job {job_id}: {description}[/info]")

        def completion_callback(completed_job_id: str, job_info: JobInfo) -> None:
            """Callback on job completion."""
            if job_info.status == JobStatus.COMPLETED:
                self.print(f"[info]Job {completed_job_id} completed successfully[/info]")

                # Update state if command dispatcher is available
                if self._command_dispatcher:
                    import asyncio

                    # Create a task to handle the async update
                    asyncio.create_task(self._command_dispatcher.handle_job_completion(completed_job_id, job_info))

            elif job_info.status == JobStatus.FAILED:
                error_msg = job_info.error if job_info.error else "Unknown error - check job details"
                self.print_error(f"Job {completed_job_id} failed: {error_msg}")
            elif job_info.status == JobStatus.CANCELLED:
                self.print(f"[info]Job {completed_job_id} was cancelled[/info]")

        try:
            # Use JobManager for true asynchronous execution
            actual_job_id = await self.job_manager.start_job(
                job_coroutine=job_coroutine,
                description=description,
                job_id=job_id,
                completion_callback=completion_callback,
                command=command,
                tool_name=tool_name,
                step_info=step_info,
            )

            # Legacy support - add to old tracking system
            from datetime import datetime

            self._running_jobs[actual_job_id] = {
                "description": description,
                "status": "running",
                "started_at": datetime.now().strftime("%H:%M:%S"),
            }

        except Exception as e:
            self.print_error(f"Failed to start job {job_id}: {e}")

    def print_step_completion(self, tool_name: str, job_id: str, success: bool) -> None:
        """Step completion notification."""
        status = "completed" if success else "failed"

        # Update job status
        if job_id in self._running_jobs:
            self._running_jobs[job_id]["status"] = status
            from datetime import datetime

            self._running_jobs[job_id]["completed_at"] = datetime.now().strftime("%H:%M:%S")

        self.print(f"[info]Step {tool_name} (job: {job_id}) {status}[/info]")

    def print_warning(self, message: str) -> None:
        """Display warning."""
        self.print(f"[warning]Warning: {message}[/warning]")

    def show_progress(self, message: str) -> None:
        """Display progress - with [▶] icon."""
        self.print(f"[info][▶] {message}[/info]")

    def show_success(self, message: str) -> None:
        """Display success - with [✔] icon."""
        self.print(f"[success][✔] {message}[/success]")

    def show_info(self, message: str) -> None:
        """Display information - with [ℹ] icon."""
        self.print(f"[info][ℹ] {message}[/info]")

    # Missing methods required by slash_commands.py and other components

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel job - using JobManager."""
        success = await self.job_manager.cancel_job(job_id)
        if success:
            # Update legacy tracking
            if job_id in self._running_jobs:
                self._running_jobs[job_id]["status"] = "cancelled"
                from datetime import datetime

                self._running_jobs[job_id]["cancelled_at"] = datetime.now().strftime("%H:%M:%S")
            self.print(f"[info]Cancelling job {job_id}[/info]")
        else:
            self.print(f"[warning]Job {job_id} not found or not running[/warning]")
        return success

    def get_job_details(self, job_id: str) -> dict[str, Any] | None:
        """Get job details - including extended information."""
        # Try JobManager first
        job_info = self.job_manager.get_job_info(job_id)
        if job_info:
            # Calculate duration
            duration = None
            if job_info.started_at:
                if job_info.completed_at:
                    duration = job_info.completed_at - job_info.started_at
                else:
                    import time

                    duration = time.time() - job_info.started_at

            # Format timestamps using local timezone
            from datetime import datetime

            started_at_str = None
            completed_at_str = None

            if job_info.started_at:
                started_at_str = datetime.fromtimestamp(job_info.started_at).strftime("%Y-%m-%d %H:%M:%S")
            if job_info.completed_at:
                completed_at_str = datetime.fromtimestamp(job_info.completed_at).strftime("%Y-%m-%d %H:%M:%S")

            details = {
                "job_id": job_info.job_id,
                "description": job_info.description,
                "status": job_info.status.value,
                "started_at": started_at_str,
                "completed_at": completed_at_str,
                "duration": f"{duration:.1f}s" if duration else None,
                "error": job_info.error,
                "command": job_info.command,
                "tool_name": job_info.tool_name,
                "exit_code": job_info.exit_code,
                "output_preview": job_info.output[:500] if job_info.output else None,
                "output_size": len(job_info.full_output) if job_info.full_output else 0,
            }

            # Add step info if available
            if job_info.step_info:
                details["purpose"] = job_info.step_info.get("purpose")
                details["parameters"] = job_info.step_info.get("parameters")

            return details

        # Fallback to legacy tracking
        return self._running_jobs.get(job_id)

    def _copy_plan_to_clipboard(self, plan: Any) -> bool:
        """Copy plan commands to clipboard."""
        try:
            # Convert plan to shell script format
            script_lines = [
                "#!/bin/bash",
                "# Generated by wish",
                f"# Plan: {getattr(plan, 'description', 'Unknown plan')}",
                "",
            ]

            if hasattr(plan, "steps"):
                for i, step in enumerate(plan.steps, 1):
                    if hasattr(step, "command") and hasattr(step, "purpose"):
                        script_lines.append(f"# Step {i}: {step.purpose}")
                        script_lines.append(step.command)
                        script_lines.append("")

            script_content = "\n".join(script_lines)

            # Copy to clipboard
            try:
                import pyperclip  # type: ignore[import-not-found]

                pyperclip.copy(script_content)
                logger.info(f"Copied {len(script_lines)} lines to clipboard")
                return True
            except ImportError:
                # Try alternative methods if pyperclip is not available
                logger.warning("pyperclip not available, trying alternative clipboard methods")
                return self._copy_to_clipboard_fallback(script_content)
            except Exception as e:
                logger.error(f"Failed to copy to clipboard with pyperclip: {e}")
                return self._copy_to_clipboard_fallback(script_content)

        except Exception as e:
            logger.error(f"Error generating script for clipboard: {e}")
            return False

    def _copy_to_clipboard_fallback(self, content: str) -> bool:
        """Fallback implementation for clipboard copy."""
        try:
            import shutil
            import subprocess

            # Try xclip (Linux)
            xclip_path = shutil.which("xclip")
            if xclip_path:
                subprocess.run([xclip_path, "-selection", "clipboard"], input=content, text=True, check=True)  # noqa: S603
                logger.info("Copied to clipboard using xclip")
                return True

            # Try xsel (Linux)
            xsel_path = shutil.which("xsel")
            if xsel_path:
                subprocess.run([xsel_path, "--clipboard", "--input"], input=content, text=True, check=True)  # noqa: S603
                logger.info("Copied to clipboard using xsel")
                return True

            # Try pbcopy (macOS)
            pbcopy_path = shutil.which("pbcopy")
            if pbcopy_path:
                subprocess.run([pbcopy_path], input=content, text=True, check=True)  # noqa: S603
                logger.info("Copied to clipboard using pbcopy")
                return True

            else:
                # Save to file if no clipboard tool is found
                logger.warning("No clipboard tool found, saving to file instead")
                import tempfile

                fd, tmp_path = tempfile.mkstemp(suffix=".sh", prefix="wish_plan_commands_")
                try:
                    with os.fdopen(fd, "w") as f:
                        f.write(content)
                    self.print(f"[info]Commands saved to {tmp_path}[/info]")
                except Exception:
                    os.close(fd)
                    raise
                return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Clipboard command failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Fallback clipboard copy failed: {e}")
            return False

    async def _edit_plan(self, plan: Any) -> Any | None:
        """Display modal for editing plan."""
        if not self._input_app:
            logger.error("MinimalInputApp not available for plan editing")
            return None

        try:
            # Display edit modal
            from wish_cli.ui.minimal_input_app import PlanEditModal

            logger.info("Displaying plan edit modal")

            # Display modal asynchronously
            async def show_edit_modal():
                edit_modal = PlanEditModal(plan)
                result = await self._input_app.push_screen_wait(edit_modal)
                return edit_modal.edited_plan if result else None

            # Execute edit modal with run_worker
            edit_result = await self._run_edit_modal_worker(show_edit_modal, plan)
            return edit_result

        except Exception as e:
            logger.error(f"Failed to edit plan: {e}")
            return None

    async def _run_edit_modal_worker(self, modal_coroutine: Any, plan: Any) -> Any:
        """Execute edit modal in worker context."""
        try:
            # Variable to store edit result
            edit_result = {"plan": None, "completed": False}

            async def edit_worker() -> None:
                try:
                    result = await modal_coroutine()
                    edit_result["plan"] = result
                    edit_result["completed"] = True
                except Exception as e:
                    logger.error(f"Edit modal worker failed: {e}")
                    edit_result["completed"] = True

            # Execute worker
            if self._input_app:
                self._input_app.run_worker(edit_worker(), exclusive=False)
            else:
                logger.error("Input app not available for edit worker")

            # Wait for completion
            import asyncio

            timeout = 300  # 5 minute timeout
            for _ in range(timeout * 10):  # Check every 0.1 seconds
                if edit_result["completed"]:
                    break
                await asyncio.sleep(0.1)

            if not edit_result["completed"]:
                logger.warning("Edit modal timed out")
                return None

            return edit_result["plan"]

        except Exception as e:
            logger.error(f"Edit modal worker execution failed: {e}")
            return None

    async def _revise_plan(self, plan: Any) -> Any | None:
        """Revise plan using AI."""
        if not self._input_app:
            logger.error("MinimalInputApp not available for plan revision")
            return None

        try:
            # Display revision request modal

            logger.info("Displaying plan revision modal")

            # Get revision request
            revision_request = await self._get_revision_request(plan)
            if revision_request is None:
                logger.info("Plan revision cancelled by user")
                return None

            # Request AI to revise plan
            return await self._generate_revised_plan(plan, revision_request)

        except Exception as e:
            logger.error(f"Failed to revise plan: {e}")
            return None

    async def _get_revision_request(self, plan: Any) -> str | None:
        """Get revision request from user."""
        try:
            from wish_cli.ui.minimal_input_app import PlanReviseModal

            # Display modal asynchronously
            async def show_revise_modal() -> str | None:
                revise_modal = PlanReviseModal(plan)
                if self._input_app:
                    result = await self._input_app.push_screen_wait(revise_modal)
                else:
                    result = None
                return result if result else None

            # Execute correction request modal with run_worker
            revision_result = await self._run_revise_modal_worker(show_revise_modal)
            return revision_result  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to get revision request: {e}")
            return None

    async def _run_revise_modal_worker(self, modal_coroutine: Any) -> Any:
        """Execute correction request modal in worker context."""
        try:
            # Variable to store revision request result
            revise_result = {"request": None, "completed": False}

            async def revise_worker() -> None:
                try:
                    result = await modal_coroutine()
                    revise_result["request"] = result
                    revise_result["completed"] = True
                except Exception as e:
                    logger.error(f"Revise modal worker failed: {e}")
                    revise_result["completed"] = True

            # Execute worker
            if self._input_app:
                self._input_app.run_worker(revise_worker(), exclusive=False)
            else:
                logger.error("Input app not available for revise worker")

            # Wait for completion
            import asyncio

            timeout = 60  # 1 minute timeout
            for _ in range(timeout * 10):  # Check every 0.1 seconds
                if revise_result["completed"]:
                    break
                await asyncio.sleep(0.1)

            if not revise_result["completed"]:
                logger.warning("Revise modal timed out")
                return None

            return revise_result["request"]

        except Exception as e:
            logger.error(f"Revise modal worker execution failed: {e}")
            return None

    async def _generate_revised_plan(self, original_plan: Any, revision_request: str) -> Any | None:
        """Generate revised plan using AI."""
        try:
            # Need access to PlanGenerator
            # Need to get from CommandDispatcher
            # Cannot directly access in current architecture,
            # Return slightly modified original plan as simpler implementation

            # TODO: Actual AI integration implementation
            # Currently only display basic revision message
            if revision_request:
                self.print(f"[info]Revision request: {revision_request}[/info]")
            else:
                self.print("[info]Generating improved plan...[/info]")

            # Temporary implementation: Add comment to original plan
            if hasattr(original_plan, "description"):
                original_plan.description += f" (Revised{': ' + revision_request if revision_request else ''})"

            self.print(
                "[warning]AI revision feature is under development. "
                "Returning original plan with revision note.[/warning]"
            )
            return original_plan

        except Exception as e:
            logger.error(f"Failed to generate revised plan: {e}")
            return None
