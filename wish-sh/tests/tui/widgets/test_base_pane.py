"""Tests for the BasePane widget."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane


class BasePaneTestApp(App):
    """Test application for BasePane."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        pane = BasePane(id="test-pane")
        yield pane
        yield Static("Test content", id="test-content")


class TestBasePane:
    """Tests for the BasePane widget."""

    @pytest.mark.asyncio
    async def test_base_pane_creation(self):
        """Test that a BasePane can be created."""
        app = BasePaneTestApp()
        async with app.run_test():
            pane = app.query_one(BasePane)
            assert pane is not None
            assert pane.id == "test-pane"

    @pytest.mark.asyncio
    async def test_base_pane_active_state(self):
        """Test that a BasePane can be set to active."""
        app = BasePaneTestApp()
        async with app.run_test():
            pane = app.query_one(BasePane)
            
            # Initially not active
            assert "active-pane" not in pane.classes
            
            # Set to active
            pane.set_active(True)
            # No need to process events, the class is added immediately
            assert "active-pane" in pane.classes
            
            # Set to inactive
            pane.set_active(False)
            # No need to process events, the class is removed immediately
            assert "active-pane" not in pane.classes
