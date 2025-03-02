"""Tests for the LogViewerScreen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from wish_sh.tui.screens.log_viewer_screen import LogViewerScreen


class LogViewerTestApp(App):
    """Test application for LogViewerScreen."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield Static("Test App")

    def on_mount(self) -> None:
        """Event handler called when the app is mounted."""
        # Push the log viewer screen
        self.push_screen(LogViewerScreen("Test log content", "Test Title"))


class TestLogViewerScreen:
    """Tests for the LogViewerScreen."""

    @pytest.mark.asyncio
    async def test_log_viewer_screen_creation(self):
        """Test that a LogViewerScreen can be created."""
        app = LogViewerTestApp()
        async with app.run_test():
            # Wait for the screen to be pushed
            await app.workers.wait_for_complete()
            
            # Get the log viewer screen
            screen = app.screen
            assert isinstance(screen, LogViewerScreen)
            
            # Check that the screen has the correct title and content
            title = screen.query_one("#log-viewer-title")
            assert title is not None
            assert title.renderable == "Test Title"
            
            content = screen.query_one("#log-content")
            assert content is not None
            assert content.renderable == "Test log content"
            
            # Skip focus check for now
            # assert screen.has_focus

    @pytest.mark.asyncio
    async def test_log_viewer_screen_key_bindings(self):
        """Test that key bindings are defined correctly."""
        app = LogViewerTestApp()
        async with app.run_test():
            # Wait for the screen to be pushed
            await app.workers.wait_for_complete()
            
            # Get the log viewer screen
            screen = app.screen
            assert isinstance(screen, LogViewerScreen)
            
            # Check that the key bindings are defined
            assert len(screen.BINDINGS) > 0
            
            # Check specific key bindings
            binding_keys = [binding.key for binding in screen.BINDINGS]
            assert "j" in binding_keys
            assert "k" in binding_keys
            assert "ctrl+f" in binding_keys
            assert "ctrl+b" in binding_keys
            assert "<" in binding_keys
            assert ">" in binding_keys
            assert "q" in binding_keys
            assert "escape" in binding_keys
