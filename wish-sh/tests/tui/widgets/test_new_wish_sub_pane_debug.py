"""Debug tests for NewWishSubPane."""

import pytest
from unittest.mock import MagicMock, patch

from wish_sh.tui.widgets.new_wish_sub_pane import NewWishSubPane


class TestNewWishSubPaneDebug:
    """Debug tests for NewWishSubPane."""

    def test_update_for_suggest_commands_with_commands(self):
        """
        TODO Remove this test (for debugging)
        
        Test that update_for_suggest_commands correctly updates content with commands.
        """
        # Create a mock sub pane
        sub_pane = NewWishSubPane()
        
        # Mock the update_content method
        sub_pane.update_content = MagicMock()
        
        # Mock the query_one method to return a mock Static widget
        mock_static = MagicMock()
        sub_pane.query_one = MagicMock(return_value=mock_static)
        
        # Test commands
        commands = ["command1", "command2"]
        
        # Call the method
        sub_pane.update_for_suggest_commands(commands)
        
        # Assert that update was called on the static widget
        mock_static.update.assert_called_once()
        
        # Check the content of the update
        update_content = mock_static.update.call_args[0][0]
        assert "[b]コマンドを確認してください[/b]" in update_content
        assert "以下のコマンドを実行しますか？ (y/n/a)" in update_content
        assert "[1] command1" in update_content
        assert "[2] command2" in update_content

    def test_update_for_suggest_commands_without_commands(self):
        """
        TODO Remove this test (for debugging)
        
        Test that update_for_suggest_commands correctly handles empty commands.
        """
        # Create a mock sub pane
        sub_pane = NewWishSubPane()
        
        # Mock the update_content method
        sub_pane.update_content = MagicMock()
        
        # Mock the query_one method to return a mock Static widget
        mock_static = MagicMock()
        sub_pane.query_one = MagicMock(return_value=mock_static)
        
        # Call the method with None
        sub_pane.update_for_suggest_commands(None)
        
        # Assert that update was called on the static widget
        mock_static.update.assert_called_once()
        
        # Check the content of the update
        update_content = mock_static.update.call_args[0][0]
        assert "[b]コマンドを確認してください[/b]" in update_content
        assert "以下のコマンドを実行しますか？ (y/n/a)" in update_content
        assert "コマンドがありません。" in update_content

    def test_update_for_suggest_commands_exception_handling(self):
        """
        TODO Remove this test (for debugging)
        
        Test that update_for_suggest_commands correctly handles exceptions.
        """
        # Create a mock sub pane
        sub_pane = NewWishSubPane()
        
        # Mock the update_content method
        sub_pane.update_content = MagicMock()
        
        # Mock the query_one method to raise an exception
        sub_pane.query_one = MagicMock(side_effect=Exception("Test exception"))
        
        # Test commands
        commands = ["command1", "command2"]
        
        # Call the method
        sub_pane.update_for_suggest_commands(commands)
        
        # Assert that update_content was called as a fallback
        sub_pane.update_content.assert_called_once()
        
        # Check the content of the update
        update_content = sub_pane.update_content.call_args[0][1]
        assert "[b]コマンドを確認してください[/b]" in update_content
        assert "以下のコマンドを実行しますか？ (y/n/a)" in update_content
        assert "[1] command1" in update_content
        assert "[2] command2" in update_content
