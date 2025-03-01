"""Tests for the MainScreen."""

import pytest
from textual.app import App, ComposeResult

from wish_sh.tui.screens.main_screen import MainScreen
from wish_sh.tui.widgets.main_pane import MainPane
from wish_sh.tui.widgets.sub_pane import SubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane


class TestApp(App):
    """Test application for MainScreen."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield MainScreen()


class TestMainScreen:
    """Tests for the MainScreen."""

    async def test_main_screen_composition(self):
        """Test that the MainScreen is composed correctly."""
        app = TestApp()
        async with app.run_test():
            # Check that the screen has the expected widgets
            screen = app.screen
            assert isinstance(screen, MainScreen)
            
            # Check that the screen has the expected panes
            wish_select = app.query_one(WishSelectPane)
            assert wish_select is not None
            assert wish_select.id == "wish-select"
            
            main_pane = app.query_one(MainPane)
            assert main_pane is not None
            assert main_pane.id == "main-pane"
            
            sub_pane = app.query_one(SubPane)
            assert sub_pane is not None
            assert sub_pane.id == "sub-pane"

    async def test_main_screen_activate_pane(self):
        """Test that the MainScreen can activate panes."""
        app = TestApp()
        async with app.run_test():
            screen = app.screen
            
            # Get the panes
            wish_select = app.query_one(WishSelectPane)
            main_pane = app.query_one(MainPane)
            sub_pane = app.query_one(SubPane)
            
            # Initially, main_pane should be active
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in main_pane.classes
            assert "active-pane" not in sub_pane.classes
            
            # Activate wish_select
            screen.activate_pane("wish-select")
            await app.process_messages()
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in main_pane.classes
            assert "active-pane" not in sub_pane.classes
            
            # Activate sub_pane
            screen.activate_pane("sub-pane")
            await app.process_messages()
            assert "active-pane" not in wish_select.classes
            assert "active-pane" not in main_pane.classes
            assert "active-pane" in sub_pane.classes
            
            # Activate main_pane
            screen.activate_pane("main-pane")
            await app.process_messages()
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in main_pane.classes
            assert "active-pane" not in sub_pane.classes
