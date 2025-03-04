"""Tests for the NewWishMainPane widget."""

import pytest
from textual.app import App, ComposeResult
from wish_models import CommandResult, CommandState, LogFiles, Wish

from wish_sh.tui.widgets.new_wish_main_pane import NewWishMainPane


class NewWishMainPaneTestApp(App):
    """Test application for NewWishMainPane."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield NewWishMainPane(id="new-wish-main-pane")


class TestNewWishMainPane:
    """Tests for the NewWishMainPane widget."""

    @pytest.mark.asyncio
    async def test_main_pane_creation(self):
        """Test that a NewWishMainPane can be created."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            assert pane is not None
            assert pane.id == "new-wish-main-pane"
            
            # Check that the pane shows the placeholder message
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert content.renderable == "(New wish content will be displayed here)"

    @pytest.mark.asyncio
    async def test_main_pane_update_for_input_wish(self):
        """Test that a NewWishMainPane can be updated for INPUT_WISH state."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            
            # Update for INPUT_WISH state
            pane.update_for_input_wish()
            
            # Check that the content has been updated
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert content.renderable == ""  # Empty content for input form

    @pytest.mark.asyncio
    async def test_main_pane_update_for_ask_wish_detail(self):
        """Test that a NewWishMainPane can be updated for ASK_WISH_DETAIL state."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            
            # Update for ASK_WISH_DETAIL state
            pane.update_for_ask_wish_detail()
            
            # Check that the content has been updated
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert "What's the target IP address or hostname?" in content.renderable

    @pytest.mark.asyncio
    async def test_main_pane_update_for_suggest_commands(self):
        """Test that a NewWishMainPane can be updated for SUGGEST_COMMANDS state."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            
            # 初期状態の内容を保存
            content_before = app.query_one("#main-pane-content").renderable
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for SUGGEST_COMMANDS state
            pane.update_for_suggest_commands(commands)
            
            # Check that the content has not been changed (main paneの内容はクリアしない)
            content_after = app.query_one("#main-pane-content").renderable
            assert content_after == content_before

    @pytest.mark.asyncio
    async def test_main_pane_update_for_adjust_commands(self):
        """Test that a NewWishMainPane can be updated for ADJUST_COMMANDS state."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for ADJUST_COMMANDS state
            pane.update_for_adjust_commands(commands)
            
            # Check that the content has been updated
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert "コマンドを修正してください" in content.renderable
            assert "コマンドリストはSub Paneで確認できます" in content.renderable

    @pytest.mark.asyncio
    async def test_main_pane_update_for_confirm_commands(self):
        """Test that a NewWishMainPane can be updated for CONFIRM_COMMANDS state."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for CONFIRM_COMMANDS state
            pane.update_for_confirm_commands(commands)
            
            # Check that the content has been updated
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert "コマンドの実行を確認してください" in content.renderable
            assert "コマンドリストはSub Paneで確認できます" in content.renderable
            assert "y/nで選択してください" in content.renderable

    @pytest.mark.asyncio
    async def test_main_pane_update_for_execute_commands(self):
        """Test that a NewWishMainPane can be updated for EXECUTE_COMMANDS state."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            
            # Create test commands
            commands = ["echo 'Hello'", "ls -la", "pwd"]
            
            # Update for EXECUTE_COMMANDS state
            pane.update_for_execute_commands(commands)
            
            # Check that the content has been updated
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert "コマンドを実行中" in content.renderable
            assert "実行中のコマンドはSub Paneで確認できます" in content.renderable

    @pytest.mark.asyncio
    async def test_main_pane_active_state(self):
        """Test that a NewWishMainPane can be set to active."""
        app = NewWishMainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(NewWishMainPane)
            
            # Initially not active
            assert "active-pane" not in pane.classes
            
            # Set to active
            pane.set_active(True)
            assert "active-pane" in pane.classes
            
            # Set to inactive
            pane.set_active(False)
            assert "active-pane" not in pane.classes
