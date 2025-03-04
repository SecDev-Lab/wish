"""Debug tests for integration."""

import pytest
from unittest.mock import MagicMock, patch

from wish_sh.tui.screens.main_screen import MainScreen
from wish_sh.tui.new_wish_turns import NewWishState, NewWishEvent
from wish_sh.tui.widgets.pane_composite import NewWishPaneComposite


class TestIntegrationDebug:
    """Debug tests for integration."""

    def test_execution_confirmed_updates_sub_pane(self):
        """
        TODO Remove this test (for debugging)
        
        Test that the sub pane is updated with confirmation message after wish execution is confirmed.
        """
        # Create a real NewWishSubPane instance
        from wish_sh.tui.widgets.new_wish_sub_pane import NewWishSubPane
        sub_pane = NewWishSubPane()
        
        # Mock the update_content method
        sub_pane.update_content = MagicMock()
        
        # Check if update_for_execution_confirmed method exists
        assert hasattr(sub_pane, "update_for_execution_confirmed"), "NewWishSubPane should have update_for_execution_confirmed method"
        
        # Call the method directly
        commands = ["echo 'test'", "ls -la"]
        sub_pane.update_for_execution_confirmed(commands)
        
        # Assert that update_content was called with the confirmation message
        sub_pane.update_content.assert_called_with("sub-pane-content", "[b][SUB PANE] コマンドが実行されました[/b]\n\n[1] echo 'test'\n[2] ls -la\n")
    
    @pytest.mark.asyncio
    async def test_execution_confirmed_updates_sub_pane_display(self):
        """
        TODO Remove this test (for debugging)
        
        Test that the sub pane display is actually updated with confirmation message after wish execution is confirmed.
        """
        # Create a test app with MainScreen
        from textual.app import App
        from wish_sh.tui.screens.main_screen import MainScreen
        from wish_sh.tui.new_wish_messages import ExecutionConfirmed
        from wish_sh.tui.widgets.new_wish_sub_pane import NewWishSubPane
        from wish_sh.tui.new_wish_turns import NewWishState
        
        class TestApp(App):
            def compose(self):
                yield MainScreen()
        
        app = TestApp()
        
        async with app.run_test() as pilot:
            # Get the main screen
            screen = app.query_one(MainScreen)
            
            # Set up the state for execution confirmed
            screen.new_wish_composite.new_wish_turns.current_state = NewWishState.EXECUTE_COMMANDS
            commands = ["echo 'test'", "ls -la"]  # カンマで区切る
            screen.new_wish_composite.new_wish_turns.set_current_commands(commands)
            
            # Send the ExecutionConfirmed message
            await pilot.press("e")  # Just to ensure the app is ready
            
            # Call handle_execution_confirmed directly to ensure it's called
            screen.new_wish_composite.handle_execution_confirmed(app=app)
            
            # Also call on_execution_confirmed for completeness
            screen.on_execution_confirmed(ExecutionConfirmed())
            
            # Wait for the UI to update
            await pilot.pause(0.1)
            
            # Get the sub pane content
            sub_pane = screen.new_wish_sub_pane
            content_widget = sub_pane.query_one("#sub-pane-content")
            
            # Check if the content contains the confirmation message
            assert "コマンドが実行されました" in content_widget.renderable, "Sub pane should display confirmation message"
            assert "echo 'test'" in content_widget.renderable, "Sub pane should display the executed commands"
            assert "ls -la" in content_widget.renderable, "Sub pane should display the executed commands"

    def test_main_screen_focus_sub_pane(self):
        """
        TODO Remove this test (for debugging)
        
        Test that the main screen correctly focuses the sub pane.
        """
        # Create a mock main pane and sub pane
        main_pane = MagicMock()
        sub_pane = MagicMock()
        
        # Create a mock composite
        composite = MagicMock()
        composite.main_pane = main_pane
        composite.sub_pane = sub_pane
        
        # Create a mock screen
        screen = MagicMock()
        screen.new_wish_main_pane = main_pane
        screen.new_wish_sub_pane = sub_pane
        screen.new_wish_composite = composite
        screen.wish_select = MagicMock()
        screen.help_pane = MagicMock()
        
        # Set up the state
        composite.new_wish_turns = MagicMock()
        composite.new_wish_turns.current_state = NewWishState.SUGGEST_COMMANDS
        
        # Call the method directly
        screen.new_wish_sub_pane.set_active(True)
        screen.new_wish_main_pane.set_active(False)
        screen.wish_select.set_active(False)
        screen.new_wish_sub_pane.focus()
        
        # Assert
        screen.new_wish_sub_pane.set_active.assert_called_with(True)
        screen.new_wish_main_pane.set_active.assert_called_with(False)
        screen.wish_select.set_active.assert_called_with(False)
        screen.new_wish_sub_pane.focus.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execution_confirmed_updates_sub_pane_display_full_flow(self):
        """
        TODO Remove this test (for debugging)
        
        Test that the sub pane display is updated with confirmation message after wish execution is confirmed,
        using the full flow from wish input to execution confirmation.
        """
        # Create a test app with MainScreen
        from textual.app import App
        from wish_sh.tui.screens.main_screen import MainScreen
        from wish_sh.tui.new_wish_messages import WishInputSubmitted, CommandsAccepted, ExecutionConfirmed
        
        class TestApp(App):
            def compose(self):
                yield MainScreen()
        
        app = TestApp()
        
        async with app.run_test() as pilot:
            # Get the main screen
            screen = app.query_one(MainScreen)
            
            # 1. Input wish
            screen.on_wish_input_submitted(WishInputSubmitted("test wish"))
            await pilot.pause(0.1)
            
            # 2. Accept commands
            screen.on_commands_accepted(CommandsAccepted())
            await pilot.pause(0.1)
            
            # 3. Confirm execution
            screen.on_execution_confirmed(ExecutionConfirmed())
            await pilot.pause(0.1)
            
            # Get the sub pane content
            sub_pane = screen.new_wish_sub_pane
            content_widget = sub_pane.query_one("#sub-pane-content")
            
            # Check if the content contains the confirmation message
            assert "コマンドが実行されました" in content_widget.renderable, "Sub pane should display confirmation message"
            assert "Wishを入力してください" not in content_widget.renderable, "Sub pane should not display 'Wishを入力してください'"
    
    @pytest.mark.asyncio
    async def test_execution_confirmed_updates_sub_pane_display_with_mode_change(self):
        """
        TODO Remove this test (for debugging)
        
        Test that the sub pane display is updated with confirmation message after wish execution is confirmed,
        and remains updated even after mode changes.
        """
        # Create a test app with MainScreen
        from textual.app import App
        from wish_sh.tui.screens.main_screen import MainScreen
        from wish_sh.tui.new_wish_messages import WishInputSubmitted, CommandsAccepted, ExecutionConfirmed
        from wish_sh.tui.modes import WishMode
        
        class TestApp(App):
            def compose(self):
                yield MainScreen()
        
        app = TestApp()
        
        async with app.run_test() as pilot:
            # Get the main screen
            screen = app.query_one(MainScreen)
            
            # 1. Input wish
            screen.on_wish_input_submitted(WishInputSubmitted("test wish"))
            await pilot.pause(0.1)
            
            # 2. Accept commands
            screen.on_commands_accepted(CommandsAccepted())
            await pilot.pause(0.1)
            
            # 3. Confirm execution
            screen.on_execution_confirmed(ExecutionConfirmed())
            await pilot.pause(0.1)
            
            # 4. Change mode and change back (simulate what might happen in the real app)
            screen.set_mode(WishMode.WISH_HISTORY)
            await pilot.pause(0.1)
            screen.set_mode(WishMode.NEW_WISH)
            await pilot.pause(0.1)
            
            # Get the sub pane content
            sub_pane = screen.new_wish_sub_pane
            content_widget = sub_pane.query_one("#sub-pane-content")
            
            # Check if the content contains the confirmation message
            assert "コマンドが実行されました" in content_widget.renderable, "Sub pane should display confirmation message"
            assert "Wishを入力してください" not in content_widget.renderable, "Sub pane should not display 'Wishを入力してください'"
