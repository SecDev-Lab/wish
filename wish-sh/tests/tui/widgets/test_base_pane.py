"""Tests for the BasePane widget."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane


class TestApp(App):
    """Test application for BasePane."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        pane = BasePane(id="test-pane")
        yield pane
        yield Static("Test content", id="test-content")


class TestBasePane:
    """Tests for the BasePane widget."""

    async def test_base_pane_creation(self):
        """Test that a BasePane can be created."""
        app = TestApp()
        async with app.run_test():
            pane = app.query_one(BasePane)
            assert pane is not None
            assert pane.id == "test-pane"

    async def test_base_pane_active_state(self):
        """Test that a BasePane can be set to active."""
        app = TestApp()
        async with app.run_test():
            pane = app.query_one(BasePane)
            
            # Initially not active
            assert "active-pane" not in pane.classes
            
            # Set to active
            pane.set_active(True)
            await app.process_messages()
            assert "active-pane" in pane.classes
            
            # Set to inactive
            pane.set_active(False)
            await app.process_messages()
            assert "active-pane" not in pane.classes
