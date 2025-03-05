"""Tests for UIUpdater."""

from unittest.mock import MagicMock

import pytest
from wish_models import CommandState
from wish_models.test_factories import WishDoingFactory

from wish_sh.tui.widgets import UIUpdater


class TestUIUpdater:
    """Tests for UIUpdater."""

    @pytest.fixture
    def screen(self):
        """Create a mock screen."""
        screen = MagicMock()

        # Mock the query_one method to return a mock widget
        status_widget = MagicMock()
        execution_text = MagicMock()

        def query_one_side_effect(selector):
            if selector == "#execution-text":
                return execution_text
            else:
                return status_widget

        screen.query_one.side_effect = query_one_side_effect

        return screen, status_widget, execution_text

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def ui_updater(self, screen):
        """Create a UIUpdater instance."""
        screen_obj, _, _ = screen
        return UIUpdater(screen_obj)

    def test_update_command_status(self, ui_updater, screen, wish):
        """Test update_command_status method.

        This test verifies that the update_command_status method correctly
        updates the UI with command statuses.
        """
        screen_obj, status_widget, _ = screen

        # Add command results to the wish
        for i in range(3):
            result = MagicMock()
            result.state = CommandState.SUCCESS
            result.exit_code = 0
            result.log_summary = f"Test summary {i + 1}"
            result.num = i + 1
            wish.command_results.append(result)

        # Update command status
        ui_updater.update_command_status(wish)

        # Verify that query_one was called for each command
        assert screen_obj.query_one.call_count == 3

        # Verify that update was called on the widget
        assert status_widget.update.call_count == 3

        # Verify that the status text contains the expected information
        for i in range(3):
            call_args = status_widget.update.call_args_list[i][0][0]
            assert f"Status: {CommandState.SUCCESS.value}" in call_args
            assert "exit code: 0" in call_args
            assert f"Summary: Test summary {i + 1}" in call_args

    def test_update_command_status_with_exit_code(self, ui_updater, screen, wish):
        """Test update_command_status method with exit code.

        This test verifies that the update_command_status method correctly
        includes the exit code in the status text.
        """
        screen_obj, status_widget, _ = screen

        # Add a command result with a non-zero exit code
        result = MagicMock()
        result.state = CommandState.OTHERS
        result.exit_code = 1
        result.log_summary = "Error occurred"
        result.num = 1
        wish.command_results.append(result)

        # Update command status
        ui_updater.update_command_status(wish)

        # Verify that query_one was called
        screen_obj.query_one.assert_called_once_with("#command-status-1")

        # Verify that update was called on the widget
        status_widget.update.assert_called_once()

        # Verify that the status text contains the expected information
        call_args = status_widget.update.call_args[0][0]
        assert f"Status: {CommandState.OTHERS.value}" in call_args
        assert "exit code: 1" in call_args
        assert "Summary: Error occurred" in call_args

    def test_update_command_status_without_log_summary(self, ui_updater, screen, wish):
        """Test update_command_status method without log summary.

        This test verifies that the update_command_status method correctly
        handles command results without a log summary.
        """
        screen_obj, status_widget, _ = screen

        # Add a command result without a log summary
        result = MagicMock()
        result.state = CommandState.SUCCESS
        result.exit_code = 0
        result.log_summary = None
        result.num = 1
        wish.command_results.append(result)

        # Update command status
        ui_updater.update_command_status(wish)

        # Verify that query_one was called
        screen_obj.query_one.assert_called_once_with("#command-status-1")

        # Verify that update was called on the widget
        status_widget.update.assert_called_once()

        # Verify that the status text contains the expected information
        call_args = status_widget.update.call_args[0][0]
        assert f"Status: {CommandState.SUCCESS.value}" in call_args
        assert "exit code: 0" in call_args
        assert "Summary:" not in call_args

    def test_show_completion_message(self, ui_updater, screen):
        """Test show_completion_message method.

        This test verifies that the show_completion_message method correctly
        updates the execution text widget with the completion message.
        """
        _, _, execution_text = screen

        # Show completion message
        message = "All commands completed."
        ui_updater.show_completion_message(message)

        # Verify that update was called on the widget
        execution_text.update.assert_called_once_with(message)
