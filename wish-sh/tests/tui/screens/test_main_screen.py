"""Tests for the MainScreen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from wish_sh.tui.screens.main_screen import MainScreen
from wish_sh.tui.widgets.main_pane import MainPane
from wish_sh.tui.widgets.sub_pane import SubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane


class MainScreenTestApp(App):
    """Test application for MainScreen."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        # Just yield a placeholder, we'll push the screen in on_mount
        yield Static("")
        
    def on_mount(self) -> None:
        """Event handler called when the app is mounted."""
        self.push_screen(MainScreen())


class TestMainScreen:
    """Tests for the MainScreen."""

    @pytest.mark.asyncio
    async def test_main_screen_composition(self):
        """Test that the MainScreen is composed correctly."""
        app = MainScreenTestApp()
        async with app.run_test():
            # Check that the screen has the expected widgets
            screen = app.query_one(MainScreen)
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

    @pytest.mark.asyncio
    async def test_main_screen_activate_pane(self):
        """Test that the MainScreen can activate panes."""
        app = MainScreenTestApp()
        async with app.run_test():
            screen = app.query_one(MainScreen)
            
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
            # No need to process events, the class is added immediately
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in main_pane.classes
            assert "active-pane" not in sub_pane.classes
            
            # Activate sub_pane
            screen.activate_pane("sub-pane")
            # No need to process events, the class is added immediately
            assert "active-pane" not in wish_select.classes
            assert "active-pane" not in main_pane.classes
            assert "active-pane" in sub_pane.classes
            
            # Activate main_pane
            screen.activate_pane("main-pane")
            # No need to process events, the class is added immediately
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in main_pane.classes
            assert "active-pane" not in sub_pane.classes
