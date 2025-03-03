"""Tests for the MainScreen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static
from wish_models import Wish

from wish_sh.tui.modes import WishMode
from wish_sh.tui.screens.main_screen import MainScreen
from wish_sh.tui.widgets.wish_history_main_pane import WishHistoryMainPane
from wish_sh.tui.widgets.wish_history_sub_pane import WishHistorySubPane
from wish_sh.tui.widgets.new_wish_main_pane import NewWishMainPane
from wish_sh.tui.widgets.new_wish_sub_pane import NewWishSubPane
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
            # Check that the screen has the expected panes
            wish_select = app.query_one(WishSelectPane)
            assert wish_select is not None
            assert wish_select.id == "wish-select"
            
            # Check that the screen has the expected mode-specific panes
            wish_history_main_pane = app.query_one(WishHistoryMainPane)
            assert wish_history_main_pane is not None
            assert wish_history_main_pane.id == "wish-history-main-pane"
            
            wish_history_sub_pane = app.query_one(WishHistorySubPane)
            assert wish_history_sub_pane is not None
            assert wish_history_sub_pane.id == "wish-history-sub-pane"
            
            new_wish_main_pane = app.query_one(NewWishMainPane)
            assert new_wish_main_pane is not None
            assert new_wish_main_pane.id == "new-wish-main-pane"
            
            new_wish_sub_pane = app.query_one(NewWishSubPane)
            assert new_wish_sub_pane is not None
            assert new_wish_sub_pane.id == "new-wish-sub-pane"

    @pytest.mark.asyncio
    async def test_main_screen_activate_pane(self):
        """Test that the MainScreen can activate panes."""
        app = MainScreenTestApp()
        async with app.run_test():
            screen = app.query_one(MainScreen)
            
            # Get the panes
            wish_select = app.query_one(WishSelectPane)
            new_wish_main_pane = app.query_one(NewWishMainPane)
            new_wish_sub_pane = app.query_one(NewWishSubPane)
            
            # Initially, new_wish_main_pane should be active and visible
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
            assert new_wish_main_pane.display == True
            assert new_wish_sub_pane.display == True
            
            # Activate wish_select
            screen.activate_pane("wish-select")
            # No need to process events, the class is added immediately
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
            
            # Activate sub_pane
            screen.activate_pane("sub-pane")
            # No need to process events, the class is added immediately
            assert "active-pane" not in wish_select.classes
            assert "active-pane" not in new_wish_main_pane.classes
            assert "active-pane" in new_wish_sub_pane.classes
            
            # Activate main_pane
            screen.activate_pane("main-pane")
            # No need to process events, the class is added immediately
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes

    @pytest.mark.asyncio
    async def test_main_screen_initial_mode(self):
        """Test that the MainScreen initializes with NEW_WISH mode."""
        app = MainScreenTestApp()
        async with app.run_test():
            screen = app.query_one(MainScreen)
            
            # Check that the screen initializes with NEW_WISH mode
            assert screen.current_mode == WishMode.NEW_WISH
            
            # Check that the new wish panes are initialized for NEW_WISH mode
            new_wish_main_pane = app.query_one(NewWishMainPane)
            assert new_wish_main_pane.query_one("#main-pane-content").renderable == ""
            
            new_wish_sub_pane = app.query_one(NewWishSubPane)
            assert "Wishを入力してください" in new_wish_sub_pane.query_one("#sub-pane-content").renderable

    @pytest.mark.asyncio
    async def test_main_screen_wish_selected_event_with_mode(self):
        """Test that the MainScreen handles WishSelected events with mode information."""
        app = MainScreenTestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(MainScreen)
            wish_history_main_pane = app.query_one(WishHistoryMainPane)
            wish_history_sub_pane = app.query_one(WishHistorySubPane)
            new_wish_main_pane = app.query_one(NewWishMainPane)
            new_wish_sub_pane = app.query_one(NewWishSubPane)
            
            # Create a test wish
            test_wish = Wish.create("Test wish for event")
            
            # Post a WishSelected event with WISH_HISTORY mode
            screen.post_message(WishSelected(test_wish, WishMode.WISH_HISTORY))
            # Wait for a frame to process the message
            await pilot.pause()
            
            # Check that the screen mode has been updated
            assert screen.current_mode == WishMode.WISH_HISTORY
            
            # Check that the wish history panes are visible and new wish panes are hidden
            assert wish_history_main_pane.display == True
            assert wish_history_sub_pane.display == True
            assert new_wish_main_pane.display == False
            assert new_wish_sub_pane.display == False
            
            # Check that the wish history main pane has been updated
            assert wish_history_main_pane.current_wish is test_wish
            
            # Check that the wish history main pane content has been updated
            main_content = wish_history_main_pane.query_one("#main-pane-content")
            assert "Wish:" in main_content.renderable
            assert "Test wish for event" in main_content.renderable
            
            # Check that the wish history sub pane has been reset
            sub_content = wish_history_sub_pane.query_one("#sub-pane-content")
            assert sub_content.renderable == "(Select a command to view details)"
            
            # Now post a WishSelected event with NEW_WISH mode
            screen.post_message(WishSelected(None, WishMode.NEW_WISH))
            # Wait for a frame to process the message
            await pilot.pause()
            
            # Check that the screen mode has been updated
            assert screen.current_mode == WishMode.NEW_WISH
            
            # Check that the new wish panes are visible and wish history panes are hidden
            assert wish_history_main_pane.display == False
            assert wish_history_sub_pane.display == False
            assert new_wish_main_pane.display == True
            assert new_wish_sub_pane.display == True
            
            # Check that the new wish main pane content has been updated
            main_content = new_wish_main_pane.query_one("#main-pane-content")
            assert main_content.renderable == ""
            
            # Check that the new wish sub pane content has been updated
            sub_content = new_wish_sub_pane.query_one("#sub-pane-content")
            assert "Wishを入力してください" in sub_content.renderable

    @pytest.mark.asyncio
    async def test_main_screen_wish_selected_focus(self):
        """Test that the MainScreen keeps focus on wish_select when a wish is selected."""
        app = MainScreenTestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(MainScreen)
            wish_select = app.query_one(WishSelectPane)
            wish_history_main_pane = app.query_one(WishHistoryMainPane)
            
            # First activate wish_select
            screen.activate_pane("wish-select")
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in wish_history_main_pane.classes
            
            # Create a test wish
            test_wish = Wish.create("Test wish for focus")
            
            # Post a WishSelected event with WISH_HISTORY mode
            screen.post_message(WishSelected(test_wish, WishMode.WISH_HISTORY))
            # Wait for a frame to process the message
            await pilot.pause()
            
            # Check that the screen mode has been updated
            assert screen.current_mode == WishMode.WISH_HISTORY
            
            # Check that the wish history main pane has been updated
            assert wish_history_main_pane.current_wish is test_wish
            
            # Check that the focus remains on wish_select
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in wish_history_main_pane.classes
    
    @pytest.mark.asyncio
    async def test_main_screen_key_navigation(self):
        """Test that the MainScreen handles key navigation."""
        app = MainScreenTestApp()
        async with app.run_test() as pilot:
            # Get the screen and panes
            screen = app.query_one(MainScreen)
            wish_select = app.query_one(WishSelectPane)
            new_wish_main_pane = app.query_one(NewWishMainPane)
            new_wish_sub_pane = app.query_one(NewWishSubPane)
            
            # Initially, new_wish_main_pane should be active
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
            
            # Directly activate wish_select
            screen.activate_pane("wish-select")
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
            
            # Directly activate main_pane
            screen.activate_pane("main-pane")
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
            
            # Directly activate sub_pane
            screen.activate_pane("sub-pane")
            assert "active-pane" not in wish_select.classes
            assert "active-pane" not in new_wish_main_pane.classes
            assert "active-pane" in new_wish_sub_pane.classes
            
            # Directly activate main_pane again
            screen.activate_pane("main-pane")
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
    
    @pytest.mark.asyncio
    async def test_main_screen_activate_pane_message(self):
        """Test that the MainScreen handles ActivatePane messages."""
        app = MainScreenTestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(MainScreen)
            
            # Get the panes
            wish_select = app.query_one(WishSelectPane)
            new_wish_main_pane = app.query_one(NewWishMainPane)
            new_wish_sub_pane = app.query_one(NewWishSubPane)
            
            # Initially, new_wish_main_pane should be active
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
            
            # Post an ActivatePane message to activate wish_select
            from wish_sh.tui.screens.main_screen import ActivatePane
            screen.post_message(ActivatePane("wish-select"))
            await pilot.pause()  # Wait for a frame to process the message
            
            # Check that wish_select is now active
            assert "active-pane" in wish_select.classes
            assert "active-pane" not in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
            
            # Post an ActivatePane message to activate sub_pane
            screen.post_message(ActivatePane("sub-pane"))
            await pilot.pause()  # Wait for a frame to process the message
            
            # Check that sub_pane is now active
            assert "active-pane" not in wish_select.classes
            assert "active-pane" not in new_wish_main_pane.classes
            assert "active-pane" in new_wish_sub_pane.classes
            
            # Post an ActivatePane message to activate main_pane
            screen.post_message(ActivatePane("main-pane"))
            await pilot.pause()  # Wait for a frame to process the message
            
            # Check that main_pane is now active
            assert "active-pane" not in wish_select.classes
            assert "active-pane" in new_wish_main_pane.classes
            assert "active-pane" not in new_wish_sub_pane.classes
    
    @pytest.mark.asyncio
    async def test_new_wish_ui_updated_on_mode_change(self):
        """Test that the UI is updated when switching to NEW_WISH mode."""
        app = MainScreenTestApp()
        async with app.run_test():
            screen = app.query_one(MainScreen)
            
            # まず別のモードに切り替える
            test_wish = Wish.create("Test wish")
            screen.set_mode(WishMode.WISH_HISTORY, test_wish)
            
            # NEW_WISHモードに切り替える
            screen.set_mode(WishMode.NEW_WISH)
            
            # new_wish_main_paneが表示されていることを確認
            new_wish_main_pane = app.query_one(NewWishMainPane)
            assert new_wish_main_pane.display == True
            
            # new_wish_sub_paneが表示されていることを確認
            new_wish_sub_pane = app.query_one(NewWishSubPane)
            assert new_wish_sub_pane.display == True
            
            # main-pane-contentが空であることを確認
            main_content = new_wish_main_pane.query_one("#main-pane-content")
            assert main_content.renderable == ""
    
    @pytest.mark.asyncio
    async def test_update_new_wish_ui_called_on_mode_change(self):
        """Test that update_new_wish_ui is called when switching to NEW_WISH mode."""
        app = MainScreenTestApp()
        async with app.run_test():
            screen = app.query_one(MainScreen)
            
            # update_new_wish_uiメソッドをモック化
            original_update_new_wish_ui = screen.update_new_wish_ui
            called = False
            
            def mock_update_new_wish_ui():
                nonlocal called
                called = True
                # 元のメソッドは呼び出さない
                return None
            
            screen.update_new_wish_ui = mock_update_new_wish_ui
            
            # まず別のモードに切り替える
            test_wish = Wish.create("Test wish")
            screen.set_mode(WishMode.WISH_HISTORY, test_wish)
            
            # calledをリセット
            called = False
            
            # NEW_WISHモードに切り替える
            screen.set_mode(WishMode.NEW_WISH)
            
            # update_new_wish_uiが呼び出されたことを確認
            assert called
            
            # 元のメソッドを復元
            screen.update_new_wish_ui = original_update_new_wish_ui
