"""Tests for the NewWishSubPane widget."""

import pytest
from textual.app import App, ComposeResult

from wish_sh.tui.widgets.new_wish_sub_pane import NewWishSubPane


class NewWishSubPaneTestApp(App):
    """Test application for NewWishSubPane."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield NewWishSubPane(id="new-wish-sub-pane")


class TestNewWishSubPane:
    """Tests for the NewWishSubPane widget."""

    @pytest.mark.asyncio
    async def test_sub_pane_creation(self):
        """Test that a NewWishSubPane can be created."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            assert pane is not None
            assert pane.id == "new-wish-sub-pane"
            
            # Check that the pane shows the placeholder message
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert content.renderable == pane.MSG_NEW_WISH_MODE

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_input_wish(self):
        """Test that a NewWishSubPane can be updated for INPUT_WISH state."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Update for INPUT_WISH state
            pane.update_for_input_wish()
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "Wishを入力してください" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_ask_wish_detail(self):
        """Test that a NewWishSubPane can be updated for ASK_WISH_DETAIL state."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Update for ASK_WISH_DETAIL state
            pane.update_for_ask_wish_detail()
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "Please enter the target IP address or hostname" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_suggest_commands(self):
        """Test that a NewWishSubPane can be updated for SUGGEST_COMMANDS state."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for SUGGEST_COMMANDS state
            pane.update_for_suggest_commands(commands)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            # main paneから移動したメッセージを確認
            assert "コマンドを確認してください" in content.renderable
            assert "以下のコマンドを実行しますか？ (y/n/a)" in content.renderable
            
            # Check that all commands are displayed
            for i, cmd in enumerate(commands, 1):
                assert f"[{i}] {cmd}" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_suggest_commands_no_commands(self):
        """Test that a NewWishSubPane can be updated for SUGGEST_COMMANDS state with no commands."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Update for SUGGEST_COMMANDS state with no commands
            pane.update_for_suggest_commands(None)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            # main paneから移動したメッセージを確認
            assert "コマンドを確認してください" in content.renderable
            assert "以下のコマンドを実行しますか？ (y/n/a)" in content.renderable
            assert "コマンドがありません" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_adjust_commands(self):
        """Test that a NewWishSubPane can be updated for ADJUST_COMMANDS state."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for ADJUST_COMMANDS state
            pane.update_for_adjust_commands(commands)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "コマンドを修正してください" in content.renderable
            
            # Check that all commands are displayed
            for i, cmd in enumerate(commands, 1):
                assert f"[{i}] {cmd}" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_adjust_commands_no_commands(self):
        """Test that a NewWishSubPane can be updated for ADJUST_COMMANDS state with no commands."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Update for ADJUST_COMMANDS state with no commands
            pane.update_for_adjust_commands(None)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "コマンドを修正してください" in content.renderable
            assert "コマンドがありません" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_confirm_commands(self):
        """Test that a NewWishSubPane can be updated for CONFIRM_COMMANDS state."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for CONFIRM_COMMANDS state
            pane.update_for_confirm_commands(commands)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "以下のコマンドを実行します。よろしいですか？ (y/n)" in content.renderable
            
            # Check that all commands are displayed
            for i, cmd in enumerate(commands, 1):
                assert f"[{i}] {cmd}" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_confirm_commands_no_commands(self):
        """Test that a NewWishSubPane can be updated for CONFIRM_COMMANDS state with no commands."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Update for CONFIRM_COMMANDS state with no commands
            pane.update_for_confirm_commands(None)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "以下のコマンドを実行します。よろしいですか？ (y/n)" in content.renderable
            assert "コマンドがありません" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_execute_commands(self):
        """Test that a NewWishSubPane can be updated for EXECUTE_COMMANDS state."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for EXECUTE_COMMANDS state
            pane.update_for_execute_commands(commands)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "コマンドを実行中です。しばらくお待ちください" in content.renderable
            
            # Check that all commands are displayed
            for i, cmd in enumerate(commands, 1):
                assert f"[{i}] {cmd}" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_execute_commands_no_commands(self):
        """Test that a NewWishSubPane can be updated for EXECUTE_COMMANDS state with no commands."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Update for EXECUTE_COMMANDS state with no commands
            pane.update_for_execute_commands(None)
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "コマンドを実行中です。しばらくお待ちください" in content.renderable
            assert "コマンドがありません" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_active_state(self):
        """Test that a NewWishSubPane can be set to active."""
        app = NewWishSubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishSubPane)
            
            # Initially not active
            assert "active-pane" not in pane.classes
            
            # Set to active
            pane.set_active(True)
            assert "active-pane" in pane.classes
            
            # Set to inactive
            pane.set_active(False)
            assert "active-pane" not in pane.classes
