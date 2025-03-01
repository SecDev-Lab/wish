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
            
            # Check that the pane has the expected content
            title = app.query_one("#main-pane-title")
            assert title is not None
            assert title.renderable == "Main Pane"
            
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
            assert "wish: Test wish" in content.renderable
            assert "Commands:" in content.renderable
            assert "echo 'Hello, world!'" in content.renderable
            assert "(DONE)" in content.renderable

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
            assert "wish: Test wish with multiple commands" in content.renderable
            
            # Check that all commands are displayed with their correct status
            assert "echo 'Command 1'" in content.renderable
            assert "(DONE)" in content.renderable
            
            assert "echo 'Command 2'" in content.renderable
            assert "(FAILED)" in content.renderable
            
            assert "echo 'Command 3'" in content.renderable
            assert "(DOING)" in content.renderable
            
            assert "echo 'Command 4'" in content.renderable
            assert "(CANCELLED)" in content.renderable

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
