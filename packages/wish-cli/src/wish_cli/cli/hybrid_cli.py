"""Hybrid CLI with modern UI using prompt_toolkit + Rich."""

import asyncio
import logging
import os

from wish_core.session import SessionManager
from wish_core.state.manager import StateManager
from wish_models.session import SessionMetadata

from wish_cli.cli.handlers.builtin import BuiltinCommandHandler
from wish_cli.cli.handlers.scope import ScopeCommandHandler
from wish_cli.cli.handlers.status import StatusCommandHandler
from wish_cli.core.command_dispatcher import CommandDispatcher
from wish_cli.ui.chat_ui_manager import ChatUIManager
from wish_cli.ui.prompt_modal import ApprovalModal, EditModal, ReviseModal
from wish_cli.ui.ui_manager import WishUIManager

logger = logging.getLogger(__name__)


class HybridWishCLI:
    """Hybrid CLI with modern UI."""

    def __init__(
        self,
        ui_manager: WishUIManager,
        command_dispatcher: CommandDispatcher,
        session_manager: SessionManager,
        state_manager: StateManager,
    ):
        self.ui_manager = ui_manager
        self.command_dispatcher = command_dispatcher
        self.session_manager = session_manager
        self.state_manager = state_manager

        self.running = False
        self.current_session: SessionMetadata | None = None

        # Create modern UI manager
        self.chat_ui = ChatUIManager(command_handler=self)

        # Command handlers
        self.builtin_handler = BuiltinCommandHandler(ui_manager=ui_manager)
        self.status_handler = StatusCommandHandler(state_manager)
        self.scope_handler = ScopeCommandHandler(state_manager)

        # Command processing sync
        self.processing_lock = asyncio.Lock()

        # Modal dialogs
        self.approval_modal = ApprovalModal(console=self.chat_ui.console)
        self.edit_modal = EditModal(console=self.chat_ui.console)
        self.revise_modal = ReviseModal(console=self.chat_ui.console)

    async def run(self) -> None:
        """Run the hybrid CLI with modern UI."""
        await self.initialize()

        try:
            self.running = True

            # Display banner
            self._display_banner()

            # Main loop
            while self.running:
                try:
                    # Get user input
                    user_input = await self.chat_ui.get_user_input()

                    if not user_input:
                        continue

                    # Debug log to check what input is received
                    logger.debug(f"Received user input: {repr(user_input)}")

                    # Process command
                    await self._handle_command_async(user_input)

                except KeyboardInterrupt:
                    self.chat_ui.print_info("\nUse /exit or 'exit' to quit")
                    continue
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    self.chat_ui.print_error(f"Error: {e}")

        except Exception as e:
            logger.error(f"CLI error: {e}")
            self.chat_ui.print_error(f"Critical error: {e}")
        finally:
            self.chat_ui.cleanup()
            await self.shutdown()

    def _display_banner(self) -> None:
        """Display welcome banner in modern style."""
        from rich.panel import Panel
        from rich.text import Text

        # Create banner content
        banner_text = Text()
        banner_text.append("✶ Welcome to ", style="bold")
        banner_text.append("wish", style="bold cyan")
        banner_text.append("!", style="bold")

        # Display in a panel
        self.chat_ui.console.print(
            Panel(
                banner_text,
                title="[bold]wish[/bold]",
                subtitle="AI-Powered Penetration Testing Assistant",
                style="yellow",
                padding=(1, 2),
            )
        )

        # Info messages
        self.chat_ui.console.print()
        self.chat_ui.console.print("[dim]/help[/dim] for help, [dim]/status[/dim] for your current setup")
        self.chat_ui.console.print("Type your commands or questions naturally")
        self.chat_ui.console.print()
        self.chat_ui.console.print(f"[dim]cwd: {os.getcwd()}[/dim]")
        self.chat_ui.console.print()

    async def _handle_command_async(self, command: str) -> None:
        """Asynchronous command processing - lightweight commands execute without lock"""
        # Determine if command is lightweight
        is_lightweight_command = self._is_lightweight_command(command)

        if is_lightweight_command:
            # Lightweight commands execute immediately without lock
            try:
                # Display user message
                self.chat_ui.print_user_message(command)

                # Handle built-in commands
                if await self._handle_builtin_command(command):
                    return

                # Handle lightweight slash commands
                if command.startswith("/"):
                    success = await self.command_dispatcher.process_command(command)
                    # None means the command was consumed (e.g., by interactive mode)
                    if success is None:
                        return
                    elif not success:
                        self.chat_ui.print_warning("Command processing failed or was cancelled")
                else:
                    self.chat_ui.print_warning("Non-slash commands require processing lock")

            except Exception as e:
                logger.error(f"Error processing lightweight command: {e}")
                self.chat_ui.print_error(f"Command processing error: {e}")
        else:
            # Heavy commands acquire lock before execution
            async with self.processing_lock:
                try:
                    # Display user message
                    self.chat_ui.print_user_message(command)

                    # Handle built-in commands
                    if await self._handle_builtin_command(command):
                        return

                    # Handle slash commands and natural language commands
                    if command.startswith("/"):
                        # Process slash commands
                        success = await self.command_dispatcher.process_command(command)
                    else:
                        # Natural language command processing
                        self.chat_ui.print_info("[dim]Generating execution plan...[/dim]")
                        success = await self.command_dispatcher.process_command(command)

                    # None means the command was consumed (e.g., by interactive mode)
                    if success is None:
                        return
                    elif not success:
                        self.chat_ui.print_warning("Command processing failed or was cancelled")

                except Exception as e:
                    logger.error(f"Error processing command: {e}")
                    self.chat_ui.print_error(f"Command processing error: {e}")

    def _is_lightweight_command(self, command: str) -> bool:
        """Determine if command is lightweight"""
        command_lower = command.lower().strip()

        # Built-in commands (always lightweight)
        builtin_commands = ["exit", "quit", "bye", "?"]
        if command_lower in builtin_commands:
            return True

        # Lightweight slash commands
        lightweight_slash_commands = [
            "/help",
            "/status",
            "/s",
            "/jobs",
            "/j",
            "/history",
            "/clear",
            "/mode",
            "/m",
            "/scope",
            "/findings",
            "/f",
            "/logs",
            "/log",
            "/config",
        ]

        for cmd in lightweight_slash_commands:
            if command_lower.startswith(cmd):
                return True

        # Natural language commands are considered heavy processing
        return False

    async def _handle_builtin_command(self, command: str) -> bool:
        """Handle built-in commands"""
        command_lower = command.lower()

        # Exit commands
        if command_lower in ["exit", "quit", "bye"]:
            self.running = False
            self.chat_ui.print_info("Goodbye!")
            return True

        # Help command
        elif command.startswith("/help") or command == "?":
            self._show_help()
            return True

        # History command
        elif command.startswith("/history"):
            self._show_history()
            return True

        # Note: /status and /scope commands are handled by command_dispatcher

        # Note: /scope command is handled by command_dispatcher
        # to support add/remove functionality

        return False

    def _show_help(self) -> None:
        """Show help information."""
        from rich.panel import Panel

        help_text = """
[bold cyan]Available Commands:[/bold cyan]

[yellow]General:[/yellow]
  /help              Show this help message
  /exit, /quit       Exit wish
  /clear             Clear the screen
  /status            Show current status

[yellow]AI & Tools:[/yellow]
  /tools             List available tools
  /model             Show/change AI model
  /provider          Show/change AI provider

[yellow]Job Management:[/yellow]
  /jobs              List running jobs
  /cancel <job_id>   Cancel a running job

[yellow]Session:[/yellow]
  /history           Show command history
  /scope             Manage target scope
  /findings          Show findings
  /export            Export conversation

[dim]Type commands or questions naturally to interact with the AI assistant.[/dim]
"""
        self.chat_ui.console.print(Panel(help_text.strip(), title="Help", style="blue", padding=(1, 2)))

    async def _show_history(self) -> None:
        """Show command history."""
        if self.state_manager:
            state = await self.state_manager.get_current_state()
            if state and state.session_metadata.command_history:
                from rich.table import Table

                table = Table(title="Command History", show_header=True, header_style="bold")
                table.add_column("#", style="dim")
                table.add_column("Command", style="cyan")

                # Show last 20 commands
                history = state.session_metadata.command_history[-20:]
                for i, cmd in enumerate(history, 1):
                    table.add_row(str(i), cmd)

                self.chat_ui.console.print(table)
            else:
                self.chat_ui.print_info("No command history available")

    async def initialize(self) -> None:
        """CLI initialization"""
        logger.info("Initializing hybrid wish CLI...")

        # Create session
        self.current_session = self.session_manager.create_session()

        # Initialize state
        await self.state_manager.initialize()

        # Initialize CommandDispatcher
        await self.command_dispatcher.initialize(self.current_session)

        logger.info("Hybrid CLI initialized successfully")

    async def shutdown(self) -> None:
        """CLI shutdown processing"""
        logger.info("Shutting down hybrid wish CLI...")

        self.running = False

        # Save session
        if self.current_session and self.state_manager:
            try:
                current_state = await self.state_manager.get_current_state()
                if current_state and self.session_manager:
                    await self.session_manager.save_session(current_state)
            except Exception as e:
                logger.error(f"Failed to save session: {e}")

        # Shutdown components
        try:
            if self.command_dispatcher and hasattr(self.command_dispatcher, "shutdown"):
                await self.command_dispatcher.shutdown()
        except Exception as e:
            logger.error(f"Failed to shutdown command dispatcher: {e}")

        try:
            if self.ui_manager and hasattr(self.ui_manager, "shutdown"):
                await self.ui_manager.shutdown()
        except Exception as e:
            logger.error(f"Failed to shutdown UI manager: {e}")

        logger.info("Hybrid CLI shutdown complete")
