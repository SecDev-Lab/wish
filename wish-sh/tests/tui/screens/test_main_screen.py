"""Tests for the MainScreen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static
from wish_models import Wish

from wish_sh.tui.screens.main_screen import MainScreen
from wish_sh.tui.widgets.main_pane import MainPane
from wish_sh.tui.widgets.sub_pane import SubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane, WishSelected


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

    @pytest.mark.asyncio
    async def test_main_screen_wish_selected_event(self):
        """Test that the MainScreen handles WishSelected events."""
        app = MainScreenTestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(MainScreen)
            main_pane = app.query_one(MainPane)
            
            # Create a test wish
            test_wish = Wish.create("Test wish for event")
            
            # Store the initial wish
            initial_wish = main_pane.current_wish
            
            # Post a WishSelected event
            screen.post_message(WishSelected(test_wish))
            # Wait for a frame to process the message
            await pilot.pause()
            
            # Now main_pane should have the new wish
            assert main_pane.current_wish is test_wish
            assert main_pane.current_wish is not initial_wish
            
            # Check that the main pane content has been updated
            content = app.query_one("#main-pane-content")
            assert "wish: Test wish for event" in content.renderable

    @pytest.mark.asyncio
    async def test_main_screen_key_navigation(self):
        """Test that the MainScreen handles key navigation."""
        app = MainScreenTestApp()
        async with app.run_test() as pilot:
            # Get the panes
            wish_select = app.query_one(WishSelectPane)
            main_pane = app.query_one(MainPane)
            sub_pane = app.query_one(SubPane)
            
            # Initially, main_pane should be active
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in main_pane.classes
            assert "active-pane" not in sub_pane.classes
            
            # Press left arrow to activate wish_select
            await pilot.press("left")
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in main_pane.classes
            assert "active-pane" not in sub_pane.classes
            
            # Press right arrow to activate main_pane
            await pilot.press("right")
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in main_pane.classes
            assert "active-pane" not in sub_pane.classes
            
            # Press ctrl+down to activate sub_pane
            await pilot.press("ctrl+down")
            assert "active-pane" not in wish_select.classes
            assert "active-pane" not in main_pane.classes
            assert "active-pane" in sub_pane.classes
            
            # Press ctrl+up to activate main_pane
            await pilot.press("ctrl+up")
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in main_pane.classes
            assert "active-pane" not in sub_pane.classes
