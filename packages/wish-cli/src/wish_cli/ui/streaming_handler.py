# wish_cli/ui/streaming_handler.py
"""
Streaming response handler for wish chat interface.
Based on modern streaming implementation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


class StreamingResponseHandler:
    """Streaming handler with live UI updates for AI responses."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.current_response = ""
        self.live_display: Live | None = None
        self.start_time = 0.0
        self.chunk_count = 0
        self.is_streaming = False
        self._response_complete = False
        self._interrupted = False

        # Tool call tracking for streaming
        self._accumulated_tool_calls: list[dict] = []
        self._current_tool_call = None

    async def stream_response(self, response_stream: AsyncIterator[str]) -> str:
        """
        Stream response from AI with live UI updates.

        Args:
            response_stream: Async iterator yielding response chunks

        Returns:
            Complete response string
        """
        self.current_response = ""
        self.chunk_count = 0
        self.start_time = time.time()
        self.is_streaming = True
        self._response_complete = False
        self._interrupted = False

        try:
            # Start live display
            self._start_live_display()

            async for chunk in response_stream:
                if self._interrupted:
                    logger.debug("Breaking from stream due to interruption")
                    break

                await self._process_chunk(chunk)

        except asyncio.CancelledError:
            logger.debug("Streaming cancelled")
            self._interrupted = True
            raise
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
        finally:
            self.is_streaming = False
            if self.live_display:
                # Show final response if not already shown
                if not self._response_complete:
                    self._show_final_response()
                self.live_display.stop()
                self.live_display = None

        return self.current_response

    def interrupt_streaming(self) -> None:
        """Interrupt the current streaming operation."""
        self._interrupted = True
        logger.debug("Streaming interrupted by user")

    def _show_final_response(self) -> None:
        """Display the final complete response with enhanced formatting."""
        if self._response_complete or not self.current_response:
            return

        elapsed = time.time() - self.start_time

        # Calculate stats
        words = len(self.current_response.split())

        # Create subtitle with stats
        subtitle_parts = [f"Response time: {elapsed:.2f}s"]
        if self.chunk_count > 1:
            subtitle_parts.append(f"Streamed: {self.chunk_count} chunks")
        if elapsed > 0:
            subtitle_parts.append(f"{words / elapsed:.1f} words/s")

        subtitle = " | ".join(subtitle_parts)

        # Format content
        try:
            # Use Markdown for formatted text
            content: Markdown | Text = Markdown(self.current_response)
        except Exception as e:
            # Fallback to Text if Markdown parsing fails
            logger.debug(f"Markdown parsing failed: {e}")
            content = Text(self.current_response)

        # Display final panel
        self.console.print(Panel(content, title="Assistant", subtitle=subtitle, style="bold blue", padding=(0, 1)))
        self._response_complete = True

    def _start_live_display(self) -> None:
        """Start the live display for streaming updates."""
        if not self.live_display:
            self.live_display = Live(
                self._create_display_content(),
                console=self.console,
                refresh_per_second=10,  # 10 FPS for smooth updates
                vertical_overflow="visible",
            )
            self.live_display.start()

    async def _process_chunk(self, chunk: str) -> None:
        """Process a single streaming chunk."""
        self.chunk_count += 1

        try:
            # Add chunk to response
            self.current_response += chunk

            # Update live display
            if self.live_display and not self._interrupted:
                self.live_display.update(self._create_display_content())

            # Small delay to prevent overwhelming the terminal
            await asyncio.sleep(0.01)

        except Exception as e:
            logger.warning(f"Error processing chunk: {e}")

    def _create_display_content(self) -> Panel:
        """Create enhanced content for live display."""
        elapsed = time.time() - self.start_time

        # Create enhanced status line
        status_text = Text()
        status_text.append("⚡ Streaming", style="cyan bold")
        status_text.append(f" • {self.chunk_count} chunks", style="dim")
        status_text.append(f" • {elapsed:.1f}s", style="dim")

        # Show performance metrics if we have enough data
        if elapsed > 1.0 and self.current_response:
            words = len(self.current_response.split())
            chars = len(self.current_response)
            words_per_sec = words / elapsed
            chars_per_sec = chars / elapsed

            status_text.append(f" • {words_per_sec:.1f} words/s", style="dim green")
            status_text.append(f" • {chars_per_sec:.0f} chars/s", style="dim green")

        # Handle interruption state
        if self._interrupted:
            status_text.append(" • INTERRUPTED", style="red bold")

        # Response content with typing cursor
        if self.current_response:
            try:
                # Progressive markdown rendering with cursor
                display_text = self.current_response
                if not self._interrupted:
                    display_text += " ▌"  # Add typing cursor
                response_content: Markdown | Text = Markdown(display_text)
            except Exception as e:
                # Fallback to plain text if markdown fails
                logger.debug(f"Markdown rendering failed: {e}")
                display_text = self.current_response
                if not self._interrupted:
                    display_text += " ▌"
                response_content = Text(display_text)
        else:
            # Show just cursor when no content yet
            cursor_style = "dim" if not self._interrupted else "red"
            response_content = Text("▌", style=cursor_style)

        # Create panel with dynamic styling
        border_style = "blue" if not self._interrupted else "red"

        return Panel(response_content, title=status_text, title_align="left", border_style=border_style, padding=(0, 1))
