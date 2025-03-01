"""Tests for the SubPane widget."""

import os
import tempfile

import pytest
from textual.app import App, ComposeResult
from wish_models import CommandResult, LogFiles

from wish_sh.tui.widgets.sub_pane import SubPane


class SubPaneTestApp(App):
    """Test application for SubPane."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield SubPane(id="sub-pane")


class TestSubPane:
    """Tests for the SubPane widget."""

    @pytest.mark.asyncio
    async def test_sub_pane_creation(self):
        """Test that a SubPane can be created."""
        app = SubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(SubPane)
            assert pane is not None
            assert pane.id == "sub-pane"
            
            # Check that the pane has the expected content
            title = app.query_one("#sub-pane-title")
            assert title is not None
            assert title.renderable == "Command Output"
            
            # Check that the pane shows the placeholder message
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert content.renderable == "(Select a command to view details)"

    @pytest.mark.asyncio
    async def test_sub_pane_update_for_new_wish_mode(self):
        """Test that a SubPane can be updated for New Wish mode."""
        app = SubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(SubPane)
            
            # Update for New Wish mode
            pane.update_for_new_wish_mode()
            
            # Check that the title has been updated
            title = app.query_one("#sub-pane-title")
            assert title is not None
            assert title.renderable == "Sub Pane (New wish mode)"
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert "新しいWishのコマンド出力がここに表示されます" in content.renderable

    @pytest.mark.asyncio
    async def test_sub_pane_update_command_output_none(self):
        """Test that a SubPane can be updated with no command result."""
        app = SubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(SubPane)
            
            # Update with no command result
            pane.update_command_output(None)
            
            # Check that the pane shows the "No command selected" message
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert content.renderable == "(No command selected)"

    @pytest.mark.asyncio
    async def test_sub_pane_update_command_output(self):
        """Test that a SubPane can be updated with a command result."""
        # Create a temporary file for stdout
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stdout_file:
            stdout_file.write("Hello, world!\n")
            stdout_path = stdout_file.name
        
        # Create a temporary file for stderr
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stderr_file:
            stderr_file.write("Error message\n")
            stderr_path = stderr_file.name
        
        try:
            # Create a test command result
            log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)
            cmd_result = CommandResult.create(1, "echo 'Hello, world!'", log_files)
            
            app = SubPaneTestApp()
            async with app.run_test():
                pane = app.query_one(SubPane)
                
                # Update with the test command result
                pane.update_command_output(cmd_result)
                
                # Check that the pane shows the command details
                content = app.query_one("#sub-pane-content")
                assert content is not None
                assert f"Command: {cmd_result.command}" in content.renderable
                assert "Standard Output:" in content.renderable
                assert "Hello, world!" in content.renderable
                assert "Standard Error:" in content.renderable
                assert "Error message" in content.renderable
        finally:
            # Clean up temporary files
            os.unlink(stdout_path)
            os.unlink(stderr_path)

    @pytest.mark.asyncio
    async def test_sub_pane_active_state(self):
        """Test that a SubPane can be set to active."""
        app = SubPaneTestApp()
        async with app.run_test():
            pane = app.query_one(SubPane)
            
            # Initially not active
            assert "active-pane" not in pane.classes
            
            # Set to active
            pane.set_active(True)
            assert "active-pane" in pane.classes
            
            # Set to inactive
            pane.set_active(False)
            assert "active-pane" not in pane.classes
