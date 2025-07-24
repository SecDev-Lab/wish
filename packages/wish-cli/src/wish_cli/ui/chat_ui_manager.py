# wish_cli/ui/chat_ui_manager.py
"""
Chat-mode UI manager for wish with modern style.
Handles prompt_toolkit input, Rich output, and streaming support.
"""

from __future__ import annotations

import logging
import os
import signal
import time
from types import FrameType
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich import print
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

from wish_cli.ui.colors import (
    ASSISTANT_COLOR,
    COMMAND_COLOR,
    STEP_COLOR,
    TEXT_ERROR,
    TEXT_INFO,
    TEXT_SUCCESS,
    TEXT_WARNING,
    TOOL_COLOR,
)
from wish_cli.ui.performance_monitor import PerformanceMonitor
from wish_cli.ui.streaming_handler import StreamingResponseHandler

logger = logging.getLogger(__name__)


class SlashCommandCompleter(Completer):
    """Completer for slash commands in wish."""

    def __init__(self, command_handler=None):
        self.command_handler = command_handler
        self.commands = [
            "/help",
            "/exit",
            "/quit",
            "/status",
            "/mode",
            "/scope",
            "/findings",
            "/jobs",
            "/logs",
            "/stop",
            "/sliver",
            "/config",
            "/history",
            "/clear",
        ]

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Only complete if we're at the start of a command
        if text.startswith("/"):
            for cmd in self.commands:
                if cmd.startswith(text):
                    yield Completion(
                        cmd, start_position=-len(text), display=cmd, display_meta=self._get_command_description(cmd)
                    )

    def _get_command_description(self, cmd: str) -> str:
        """Get description for a command."""
        descriptions = {
            "/help": "Show available commands",
            "/exit": "Exit wish",
            "/quit": "Exit wish",
            "/status": "Show current engagement status",
            "/mode": "Change current mode",
            "/scope": "Manage target scope",
            "/findings": "Show current findings",
            "/jobs": "Show running jobs",
            "/logs": "Show logs for a specific job",
            "/stop": "Stop a running job",
            "/sliver": "Interact with Sliver C2",
            "/config": "Show configuration",
            "/history": "Show command history",
            "/clear": "Clear the screen",
        }
        return descriptions.get(cmd, "")


class ChatUIManager:
    """Interactive UI layer with modern style display and streaming support."""

    def __init__(self, command_handler=None):
        self.command_handler = command_handler

        # Create custom theme
        custom_theme = Theme(
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

        self.console = Console(theme=custom_theme)
        self.streaming_handler = StreamingResponseHandler(self.console)
        self.performance_monitor = PerformanceMonitor(self.console)

        self.verbose_mode = False
        self.tools_running = False
        self.interrupt_requested = False

        self.tool_calls: list[dict[str, Any]] = []
        self.tool_times: list[float] = []
        self.tool_start_time: float | None = None
        self.current_tool_start_time: float | None = None

        self.live_display: Live | None = None
        self.spinner_frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.spinner_idx = 0

        self._prev_sigint_handler: signal.Handlers | None = None
        self._interrupt_count = 0
        self._last_interrupt_time = 0

        try:
            style = Style.from_dict(
                {
                    "completion-menu": "bg:default",
                    "completion-menu.completion": "bg:default fg:goldenrod",
                    "completion-menu.completion.current": "bg:default fg:goldenrod bold",
                    "auto-suggestion": "fg:ansibrightblack",
                }
            )

            # Set up history
            history_path = os.path.expanduser("~/.wish/chat_history")
            os.makedirs(os.path.dirname(history_path), exist_ok=True)

            self.session = PromptSession(
                history=FileHistory(history_path),
                auto_suggest=AutoSuggestFromHistory(),
                completer=SlashCommandCompleter(command_handler),
                complete_while_typing=True,
                style=style,
                message="> ",
            )
        except Exception as e:
            logger.error(f"Error initializing prompt session: {e}")
            self.session = None

        self.last_input: str | None = None

    # Signal handling methods
    def _install_sigint_handler(self) -> None:
        """Install SIGINT handler with error protection."""
        try:
            if self._prev_sigint_handler is not None:
                return

            try:
                self._prev_sigint_handler = signal.getsignal(signal.SIGINT)
            except (ValueError, TypeError) as sig_err:
                logger.warning(f"Could not get current signal handler: {sig_err}")
                return

            def _handler(sig: int, frame: FrameType | None):
                try:
                    current_time = time.time()

                    if current_time - self._last_interrupt_time > 2.0:
                        self._interrupt_count = 0

                    self._last_interrupt_time = current_time
                    self._interrupt_count += 1

                    # Handle streaming response interruption
                    if self.streaming_handler.is_streaming:
                        print("\n[yellow]Interrupting streaming response...[/yellow]")
                        self.streaming_handler.interrupt_streaming()
                        return

                    # Handle tool execution interruption
                    if self.tools_running or self.interrupt_requested:
                        if self.tools_running and not self.interrupt_requested:
                            self.interrupt_requested = True
                            print("\n[yellow]Interrupt requested - cancelling current tool execution…[/yellow]")
                            self._interrupt_now()

                        if self.tools_running and self._interrupt_count >= 2:
                            print("\n[red]Force terminating current operation...[/red]")
                            self.stop_tool_calls()
                            print("[yellow]Tool execution forcefully stopped.[/yellow]")

                        return

                    # Idle - propagate to default handler
                    prev_handler = self._prev_sigint_handler
                    if callable(prev_handler):
                        prev_handler(sig, frame)
                except Exception as exc:
                    logger.error(f"Error in signal handler: {exc}")
                    print(f"[red]Error in signal handler: {exc}[/red]")

            try:
                signal.signal(signal.SIGINT, _handler)
            except Exception as set_err:
                logger.warning(f"Could not set signal handler: {set_err}")
                self._prev_sigint_handler = None
        except Exception as exc:
            logger.error(f"Error in signal handler setup: {exc}")

    def _restore_sigint_handler(self) -> None:
        """Restore the original SIGINT handler."""
        try:
            if self._prev_sigint_handler:
                try:
                    signal.signal(signal.SIGINT, self._prev_sigint_handler)
                    self._prev_sigint_handler = None
                except Exception as e:
                    logger.warning(f"Error restoring signal handler: {e}")
        except Exception as exc:
            logger.error(f"Error in _restore_sigint_handler: {exc}")

    def _interrupt_now(self) -> None:
        """Called on first Ctrl-C to cancel operations."""
        try:
            if self.command_handler and hasattr(self.command_handler, "cancel_operations"):
                self.command_handler.cancel_operations()

            self.stop_tool_calls()
        except Exception as exc:
            logger.error(f"Error in _interrupt_now: {exc}")

    # Input/Output methods
    async def get_user_input(self) -> str:
        """Get user input with error handling and fallbacks."""
        try:
            if self.session is None:
                # Fallback to basic input
                import asyncio

                user_input = await asyncio.to_thread(input, "> ")
                self.last_input = user_input.strip()
                return self.last_input

            msg = await self.session.prompt_async()
            self.last_input = msg.strip()

            # Debug logging
            logger.debug(f"ChatUIManager.get_user_input received: {repr(self.last_input)}")

            try:
                print("\r" + " " * (len(self.last_input) + 2), end="\r")
            except Exception:  # noqa: S110
                pass
            return self.last_input
        except EOFError:
            logger.info("EOF received in get_user_input, returning empty string")
            return ""
        except Exception as exc:
            logger.error(f"Error getting user input: {exc}")
            import asyncio

            try:
                return await asyncio.to_thread(input, "> ")
            except Exception:
                return ""

    def print_user_message(self, message: str) -> None:
        """Display user message in modern style."""
        try:
            # Simply print the message without a box
            # print(f"[{USER_COLOR}]> {message or '[No Message]'}[/{USER_COLOR}]")
            # Actually, don't print anything - the prompt already shows what the user typed
            self.tool_calls.clear()
            if not self.verbose_mode:
                self.live_display = None
        except Exception as exc:
            logger.error(f"Error printing user message: {exc}")

    def print_tool_call(self, tool_name: str, args: Any) -> None:
        """Display a tool call in modern style."""
        try:
            # Don't show if streaming
            if self.streaming_handler.is_streaming:
                return

            # Start timing
            if not self.tool_start_time:
                self.tool_start_time = time.time()
                self.tools_running = True
                self._install_sigint_handler()

            # Record time for previous tool
            if self.current_tool_start_time and self.tool_calls:
                self.tool_times.append(time.time() - self.current_tool_start_time)
            self.current_tool_start_time = time.time()

            # Add to tracking
            self.tool_calls.append({"name": tool_name, "args": args})

            # Skip if interrupted
            if self.interrupt_requested:
                return

            # Display based on mode
            if self.verbose_mode:
                self._display_verbose_tool_call(tool_name, args)
            else:
                self._display_compact_tool_calls()
        except Exception as exc:
            logger.error(f"Error displaying tool call: {exc}")
            print(f"[{TOOL_COLOR}]Running tool:[/{TOOL_COLOR}] {tool_name}")

    def _display_verbose_tool_call(self, tool_name: str, args: Any) -> None:
        """Display verbose tool call information."""
        try:
            import json

            args_json = json.dumps(args, indent=2) if isinstance(args, dict) else str(args)
            md = f"**Tool Call:** {tool_name}\n\n```json\n{args_json}\n```"

            try:
                markdown_content = Markdown(md)
                print(Panel(markdown_content, style=f"bold {TOOL_COLOR}", title="Tool Invocation"))
            except Exception:
                message_text = Text(f"Tool Call: {tool_name}\n\n{args_json}")
                print(Panel(message_text, style=f"bold {TOOL_COLOR}", title="Tool Invocation"))
        except Exception:
            print(f"[{TOOL_COLOR}]Tool Call:[/{TOOL_COLOR}] {tool_name}")
            print(f"[dim]Arguments:[/dim] {str(args)}")

    def _display_compact_tool_calls(self) -> None:
        """Display compact view of tool calls."""
        try:
            if self.live_display is None:
                try:
                    self.live_display = Live("", refresh_per_second=4, console=self.console)
                    self.live_display.start()
                    print("[dim italic]Press Ctrl+C to interrupt tool execution[/dim italic]", end="\r")
                except Exception as live_exc:
                    logger.warning(f"Could not create live display: {live_exc}")
                    print(f"[{TOOL_COLOR}]Running tool:[/{TOOL_COLOR}] {self.tool_calls[-1]['name']}")
                    return

            # Calculate times
            now = time.time()
            cur_elapsed = int(now - (self.current_tool_start_time or now))
            total_elapsed = int(now - (self.tool_start_time or now))

            # Get spinner
            spinner = self._get_spinner_char()

            # Build display
            parts: list[str] = []

            # Completed tools
            for i, t in enumerate(self.tool_calls[:-1]):
                name = t.get("name", "unknown")
                dur = f" ({self.tool_times[i]:.1f}s)" if i < len(self.tool_times) else ""
                parts.append(f"[dim green]{i + 1}. {name}{dur}[/dim green]")

            # Current tool
            if self.tool_calls:
                idx = len(self.tool_calls) - 1
                name = self.tool_calls[-1].get("name", "unknown")
                parts.append(f"[{TOOL_COLOR}]{idx + 1}. {name} ({cur_elapsed}s)[/{TOOL_COLOR}]")

            # Update display
            separator = " → "
            display_text = Text.from_markup(
                f"[dim]Calling tools (total: {total_elapsed}s): {spinner}[/dim] " + separator.join(parts)
            )
            self.live_display.update(display_text)

        except Exception as exc:
            logger.error(f"Error in compact display: {exc}")

    def _get_spinner_char(self) -> str:
        """Get the next spinner frame."""
        try:
            ch = self.spinner_frames[self.spinner_idx]
            self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_frames)
            return ch
        except Exception:
            return "*"

    def print_assistant_response(self, content: str, elapsed: float) -> None:
        """Display assistant response in modern style."""
        try:
            # If streaming was used, response is already displayed
            if self.streaming_handler.is_streaming:
                self.streaming_handler.stop_streaming_response()
                return

            # Clean up tool display
            if not self.verbose_mode and self.live_display:
                try:
                    self.live_display.stop()
                    self.live_display = None
                except Exception as live_exc:
                    logger.warning(f"Error stopping live display: {live_exc}")

                # Show completion time
                if self.tool_start_time:
                    print(f"[dim]Tools completed in {time.time() - self.tool_start_time:.2f}s total[/dim]")

                # Reset state
                self.interrupt_requested = False
                self.stop_tool_calls()
                self._restore_sigint_handler()

            # Display response
            try:
                if "[/" in content or "\\[" in content:
                    response_content = Text(content or "[No Response]")
                else:
                    try:
                        response_content = Markdown(content or "[No Response]")
                    except Exception:
                        response_content = Text(content or "[No Response]")

                print(
                    Panel(
                        response_content,
                        style=f"bold {ASSISTANT_COLOR}",
                        title="Assistant",
                        subtitle=f"Response time: {elapsed:.2f}s",
                    )
                )
            except Exception as panel_exc:
                logger.error(f"Error creating response panel: {panel_exc}")
                print(f"\n[bold {ASSISTANT_COLOR}]Assistant:[/bold {ASSISTANT_COLOR}]")
                print(content or "[No Response]")
                print(f"[dim]Response time: {elapsed:.2f}s[/dim]")

        except Exception as exc:
            logger.error(f"Error displaying assistant response: {exc}")
            print("Assistant:")
            print(content or "[No Response]")
            print(f"Response time: {elapsed:.2f}s")

    def stop_tool_calls(self) -> None:
        """Stop all running tool calls and clean up displays."""
        try:
            if self.live_display:
                try:
                    self.live_display.stop()
                except Exception as live_exc:
                    logger.warning(f"Error stopping live display: {live_exc}")
                self.live_display = None

            self.tools_running = False
            self.tool_start_time = None
            self.current_tool_start_time = None
            self.tool_times.clear()
        except Exception as exc:
            logger.error(f"Error in stop_tool_calls: {exc}")

    def print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[info]{message}[/info]")

    def print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[error]{message}[/error]")

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[success]{message}[/success]")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[warning]{message}[/warning]")

    def clear_screen(self) -> None:
        """Clear the console screen."""
        self.console.clear()

    async def handle_command(self, cmd: str) -> bool:
        """Process a slash command."""
        if self.command_handler:
            return await self.command_handler.handle_command(cmd)
        return False

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.live_display:
                try:
                    self.live_display.stop()
                except Exception:  # noqa: S110
                    pass
                self.live_display = None

            self._restore_sigint_handler()
        except Exception as exc:
            logger.error(f"Error during UI cleanup: {exc}")
