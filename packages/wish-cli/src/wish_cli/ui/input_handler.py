"""Input handling and command completion system."""

import asyncio
import logging
from contextlib import suppress
from typing import Any

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import CompleteStyle

logger = logging.getLogger(__name__)


class WishCompleter(Completer):
    """Wish-specific completion system."""

    def __init__(self, state_manager: Any = None, tool_registry: Any = None) -> None:
        self.state_manager = state_manager
        self.tool_registry = tool_registry

        # Basic commands
        self.slash_commands = [
            "/help",
            "/status",
            "/mode",
            "/scope",
            "/findings",
            "/sliver",
            "/config",
            "/history",
            "/clear",
            "/logs",
            "/jobs",
            "/stop",
        ]

        # Available modes
        self.modes = ["recon", "enum", "exploit", "report"]

        # Commonly used tools
        self.common_tools = ["nmap", "nikto", "gobuster", "dirb", "sqlmap", "hydra", "john", "hashcat", "enum4linux"]

        # Natural language phrases
        self.common_phrases = [
            "scan the target",
            "enumerate web directories",
            "check for vulnerabilities",
            "run a port scan",
            "test for SQL injection",
            "brute force login",
            "escalate privileges",
            "deploy sliver implant",
        ]

    def get_completions(self, document: Any, complete_event: Any) -> list[Completion]:
        """Generate completion candidates."""
        text = document.text_before_cursor
        completions = []

        # Slash command completion
        if text.startswith("/"):
            for cmd in self.slash_commands:
                if cmd.startswith(text):
                    completions.append(Completion(cmd, start_position=-len(text)))

        # Mode completion
        elif text.startswith("/mode "):
            mode_text = text[6:]
            for mode in self.modes:
                if mode.startswith(mode_text):
                    completions.append(Completion(mode, start_position=-len(mode_text)))

        # Tool name completion
        elif any(tool in text for tool in self.common_tools):
            completions.extend(self._tool_specific_completion(text))

        # Natural language completion
        else:
            completions.extend(self._natural_language_completion(text))

        return completions

    def _slash_command_completion(self, text: str) -> list[str]:
        """Slash command completion."""
        # Basic command completion
        completions = []
        for cmd in self.slash_commands:
            if cmd.startswith(text):
                completions.append(cmd)
        return completions

    def _tool_specific_completion(self, text: str) -> list[Completion]:
        """Tool-specific completion."""
        completions = []

        # nmap completion
        if "nmap" in text:
            nmap_options = ["-sS", "-sT", "-sU", "-sV", "-sC", "-O", "-A", "-p", "-oX", "-oN", "-T4", "--script"]
            for option in nmap_options:
                if text.endswith(" ") or option.startswith(text.split()[-1]):
                    completions.append(Completion(option))

        # gobuster completion
        elif "gobuster" in text:
            gobuster_options = ["dir", "dns", "vhost", "-u", "-w", "-x", "-t", "-o"]
            for option in gobuster_options:
                if text.endswith(" ") or option.startswith(text.split()[-1]):
                    completions.append(Completion(option))

        return completions

    def _natural_language_completion(self, text: str) -> list[Completion]:
        """Natural language completion."""
        completions = []
        for phrase in self.common_phrases:
            if phrase.startswith(text.lower()):
                completions.append(Completion(phrase, start_position=-len(text)))
        return completions


class AsyncInputHandler:
    """Asynchronous input processing."""

    def __init__(self, ui_manager: Any, completer: WishCompleter) -> None:
        self.ui_manager = ui_manager
        self.completer = completer
        self.input_queue: asyncio.Queue[str] = asyncio.Queue()
        self.input_task: asyncio.Task | None = None
        self.running = False

        # History management
        self.history: list[str] = []
        self.history_index = 0
        self.prompt_history: list[str] = []

        # Prompt settings (no longer needed due to Claude Code-style panels, but kept for compatibility)
        self.prompt_text = ""

    async def start(self) -> None:
        """Start input processing."""
        self.running = True
        self.input_task = asyncio.create_task(self._input_worker())
        logger.debug("Input handler started")

    async def stop(self) -> None:
        """Stop input processing."""
        self.running = False
        if self.input_task and not self.input_task.done():
            self.input_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.input_task
        logger.debug("Input handler stopped")

    async def get_user_input(self) -> str:
        """Get user input."""
        if not self.running:
            return "exit"
        try:
            return await self.input_queue.get()
        except Exception as e:
            logger.error(f"Failed to get user input: {e}")
            return "exit"

    async def _input_worker(self) -> None:
        """Input worker."""
        while self.running:
            try:
                # Use prompt_toolkit for advanced input
                user_input = await self._get_input_async()

                if user_input:
                    # Add to history
                    self.history.append(user_input)
                    self.history_index = len(self.history)
                    self.prompt_history.append(user_input)

                    # Add to queue
                    await self.input_queue.put(user_input)

            except (KeyboardInterrupt, EOFError):
                await self.input_queue.put("exit")
                break
            except Exception as e:
                logger.error(f"Input error: {e}")
                # Continue even if error occurs
                await asyncio.sleep(0.1)

    async def _get_input_async(self) -> str:
        """Asynchronous input acquisition."""
        if not self.running:
            return "exit"

        loop = asyncio.get_event_loop()
        if loop is None:
            logger.error("No event loop available")
            return "exit"

        # Use prompt_toolkit for advanced input
        try:
            result = await loop.run_in_executor(None, lambda: self._get_input_with_prompt_toolkit())
            return result if result is not None else ""
        except (KeyboardInterrupt, EOFError):
            return "exit"
        except Exception as e:
            logger.error(f"Input error: {e}")
            return "exit"

    def _get_input_with_prompt_toolkit(self) -> str:
        """Advanced input using prompt toolkit (Claude Code style)."""
        try:
            # Check if we're in a real terminal
            import sys

            if not sys.stdin.isatty():
                # Not a terminal, use fallback
                return self._get_input_fallback()

            # Key binding setup
            kb = KeyBindings()

            @kb.add(Keys.ControlC)
            def _(event: Any) -> None:
                """First Ctrl+C: clear input, second: exit"""
                if hasattr(event.app, "ctrl_c_count"):
                    event.app.ctrl_c_count += 1
                    if event.app.ctrl_c_count >= 2:
                        event.app.exit(exception=KeyboardInterrupt)
                    else:
                        event.current_buffer.reset()
                else:
                    event.app.ctrl_c_count = 1
                    event.current_buffer.reset()

            @kb.add(Keys.ControlR)
            def _(event: Any) -> None:
                """History search"""
                # TODO: Implement history search functionality
                pass

            @kb.add(Keys.ControlE)
            def _(event: Any) -> None:
                """Command editing"""
                # TODO: Implement command editing functionality
                pass

            # History management
            history = InMemoryHistory()
            for item in self.prompt_history:
                history.append_string(item)

            # Execute prompt (Claude Code style simple settings)
            user_input = prompt(
                "",  # Prompt already displayed in input panel
                completer=self.completer,
                complete_style=CompleteStyle.MULTI_COLUMN,
                history=history,
                key_bindings=kb,
                mouse_support=False,  # Claude Code style simple setting
                wrap_lines=True,
                multiline=False,  # Claude Code style simple setting
                enable_history_search=True,
            )

            return user_input
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            logger.error(f"Prompt toolkit input error: {e}")
            # Use standard input as fallback
            return self._get_input_fallback()

    def _get_input_fallback(self) -> str:
        """Fallback input processing."""
        try:
            result = input("> ")  # Simple prompt
            logger.info(f"Fallback input received: {result}")
            return result
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            logger.error(f"Fallback input error: {e}")
            return ""
