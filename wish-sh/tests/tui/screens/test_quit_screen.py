"""Tests for the QuitScreen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button

from wish_sh.tui.screens.quit_screen import QuitScreen


class TestApp(App):
    """Test application for QuitScreen."""

    def __init__(self):
        """Initialize the test application."""
        super().__init__()
        self.exit_called = False

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield QuitScreen()

    def exit(self, *args, **kwargs):
        """Override exit to track when it's called."""
        self.exit_called = True


class TestQuitScreen:
    """Tests for the QuitScreen."""

    async def test_quit_screen_composition(self):
        """Test that the QuitScreen is composed correctly."""
        app = TestApp()
        async with app.run_test():
            # Check that the screen has the expected widgets
            screen = app.screen
            assert isinstance(screen, QuitScreen)
            
            # Check that the screen has the expected buttons
            yes_button = app.query_one("#yes")
            assert yes_button is not None
            assert isinstance(yes_button, Button)
            assert yes_button.label == "はい"
            
            no_button = app.query_one("#no")
            assert no_button is not None
            assert isinstance(no_button, Button)
            assert no_button.label == "いいえ"

    async def test_quit_screen_yes_button(self):
        """Test that the yes button exits the application."""
        app = TestApp()
        async with app.run_test():
            # Press the yes button
            yes_button = app.query_one("#yes")
            await yes_button.press()
            
            # Check that exit was called
            assert app.exit_called is True

    async def test_quit_screen_no_button(self):
        """Test that the no button pops the screen."""
        app = TestApp()
        
        # Mock the pop_screen method
        original_pop_screen = app.pop_screen
        pop_screen_called = False
        
        def mock_pop_screen(*args, **kwargs):
            nonlocal pop_screen_called
            pop_screen_called = True
            return original_pop_screen(*args, **kwargs)
        
        app.pop_screen = mock_pop_screen
        
        async with app.run_test():
            # Press the no button
            no_button = app.query_one("#no")
            await no_button.press()
            
            # Check that pop_screen was called
            assert pop_screen_called is True
            
            # Check that exit was not called
            assert app.exit_called is False
