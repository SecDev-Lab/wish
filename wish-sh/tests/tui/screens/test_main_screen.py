"""Tests for the MainScreen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static
from wish_models import Wish

from wish_sh.tui.modes import WishMode
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
    async def test_main_screen_initial_mode(self):
        """Test that the MainScreen initializes with NEW_WISH mode."""
        app = MainScreenTestApp()
        async with app.run_test():
            screen = app.query_one(MainScreen)
            
            # Check that the screen initializes with NEW_WISH mode
            assert screen.current_mode == WishMode.NEW_WISH
            
            # Check that the main pane is initialized for NEW_WISH mode
            main_content = app.query_one("#main-pane-content")
            assert "新しいWishを作成するモードです" in main_content.renderable
            
            # Check that the sub pane is initialized for NEW_WISH mode
            sub_content = app.query_one("#sub-pane-content")
            assert "新しいWishのコマンド出力がここに表示されます" in sub_content.renderable

    @pytest.mark.asyncio
    async def test_main_screen_wish_selected_event_with_mode(self):
        """Test that the MainScreen handles WishSelected events with mode information."""
        app = MainScreenTestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(MainScreen)
            main_pane = app.query_one(MainPane)
            sub_pane = app.query_one(SubPane)
            
            # Create a test wish
            test_wish = Wish.create("Test wish for event")
            
            # Post a WishSelected event with WISH_HISTORY mode
            screen.post_message(WishSelected(test_wish, WishMode.WISH_HISTORY))
            # Wait for a frame to process the message
            await pilot.pause()
            
            # Check that the screen mode has been updated
            assert screen.current_mode == WishMode.WISH_HISTORY
            
            # Check that the main pane has been updated
            assert main_pane.current_wish is test_wish
            
            # Check that the main pane content has been updated
            main_content = app.query_one("#main-pane-content")
            assert "wish: Test wish for event" in main_content.renderable
            
            # Check that the sub pane has been reset
            sub_content = app.query_one("#sub-pane-content")
            assert sub_content.renderable == "(Select a command to view details)"
            
            # Now post a WishSelected event with NEW_WISH mode
            screen.post_message(WishSelected(None, WishMode.NEW_WISH))
            # Wait for a frame to process the message
            await pilot.pause()
            
            # Check that the screen mode has been updated
            assert screen.current_mode == WishMode.NEW_WISH
            
            # Check that the main pane content has been updated
            main_content = app.query_one("#main-pane-content")
            assert "新しいWishを作成するモードです" in main_content.renderable
            
            # Check that the sub pane content has been updated
            sub_content = app.query_one("#sub-pane-content")
            assert "新しいWishのコマンド出力がここに表示されます" in sub_content.renderable

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
