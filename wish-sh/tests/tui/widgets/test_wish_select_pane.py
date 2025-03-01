"""Tests for the WishSelectPane widget."""

import pytest
from textual.app import App, ComposeResult
from textual.pilot import Pilot
from wish_models import Wish

from wish_sh.tui.modes import WishMode
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane, WishSelected


class WishSelectPaneTestApp(App):
    """Test application for WishSelectPane."""

    def __init__(self, wishes=None):
        """Initialize the test application.
        
        Args:
            wishes: List of wishes to display.
        """
        super().__init__()
        self.wishes = wishes

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield WishSelectPane(wishes=self.wishes, id="wish-select")


class TestWishSelectPane:
    """Tests for the WishSelectPane widget."""

    @pytest.mark.asyncio
    async def test_wish_select_pane_creation(self):
        """Test that a WishSelectPane can be created."""
        app = WishSelectPaneTestApp()
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            assert pane is not None
            assert pane.id == "wish-select"
            
            # Check that the pane shows the "No wishes available" message
            content = app.query_one("#wish-select-content")
            assert content is not None
            assert content.renderable == "(No wishes available)"

    @pytest.mark.asyncio
    async def test_wish_select_pane_with_wishes(self):
        """Test that a WishSelectPane can display wishes."""
        # Create some test wishes
        test_wishes = [
            Wish.create("Wish 1"),
            Wish.create("Wish 2"),
            Wish.create("Wish 3")
        ]
        
        app = WishSelectPaneTestApp(wishes=test_wishes)
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            assert pane is not None
            
            # Check that the pane shows the NEW WISH option and the wishes
            statics = app.query("Static")
            assert len(statics) == len(test_wishes) + 1  # +1 for NEW WISH option
            
            # The first Static is the NEW WISH option
            assert "NEW WISH" in statics[0].renderable
            
            # The rest are the wishes
            for i, wish in enumerate(test_wishes, 1):  # Start from index 1 (after NEW WISH)
                assert wish.wish in statics[i].renderable

    @pytest.mark.asyncio
    async def test_wish_select_pane_active_state(self):
        """Test that a WishSelectPane can be set to active."""
        app = WishSelectPaneTestApp()
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            
            # Initially not active
            assert "active-pane" not in pane.classes
            
            # Set to active
            pane.set_active(True)
            # No need to process events, the class is added immediately
            assert "active-pane" in pane.classes
            
            # Set to inactive
            pane.set_active(False)
            # No need to process events, the class is removed immediately
            assert "active-pane" not in pane.classes

    @pytest.mark.asyncio
    async def test_wish_select_pane_with_real_wishes(self):
        """Test that a WishSelectPane can display real Wish objects."""
        # Create some test Wish objects
        test_wishes = [
            Wish.create("Test wish 1"),
            Wish.create("Test wish 2"),
            Wish.create("Test wish 3")
        ]
        
        app = WishSelectPaneTestApp(wishes=test_wishes)
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            assert pane is not None
            
            # Check that the pane shows the wishes
            statics = app.query("Static")
            assert len(statics) == len(test_wishes) + 1  # +1 for NEW WISH option
            
            # The wishes start at index 1 (after NEW WISH option)
            for i, wish in enumerate(test_wishes, 0):
                # Check that the text contains the wish text
                wish_index = i + 1  # Adjust for NEW WISH option
                assert wish.wish in statics[wish_index].renderable

    @pytest.mark.asyncio
    async def test_wish_select_pane_with_brackets(self):
        """Test that a WishSelectPane can display text with brackets correctly."""
        # Create a Wish with brackets in the text
        test_wish = Wish.create("[This is a wish with brackets]")
        
        app = WishSelectPaneTestApp(wishes=[test_wish])
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            assert pane is not None
            
            # Check that the pane shows the wish with brackets
            statics = app.query("Static")
            assert len(statics) == 2  # NEW WISH option + 1 wish
            
            # The wish text should contain the brackets (at index 1, after NEW WISH)
            assert "[This is a wish with brackets]" in statics[1].renderable
    
    @pytest.mark.asyncio
    async def test_new_wish_option_display(self):
        """Test that the NEW WISH option is displayed correctly."""
        app = WishSelectPaneTestApp()
        async with app.run_test():
            # Check that the NEW WISH option is displayed
            new_wish_option = app.query_one("#new-wish-option")
            assert new_wish_option is not None
            assert "NEW WISH" in new_wish_option.renderable
            
            # Check that it has the sparkles emoji
            assert "✨" in new_wish_option.renderable
            
            # Check that it's selected by default
            assert "selected" in new_wish_option.classes

    @pytest.mark.asyncio
    async def test_wish_selection_with_keys(self):
        """Test that wishes can be selected using up/down keys."""
        # Create some test wishes
        test_wishes = [
            Wish.create("Wish 1"),
            Wish.create("Wish 2"),
            Wish.create("Wish 3")
        ]
        
        app = WishSelectPaneTestApp(wishes=test_wishes)
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            
            # Initially, the NEW WISH option should be selected
            assert pane.selected_index == 0
            new_wish_option = app.query_one("#new-wish-option")
            assert "selected" in new_wish_option.classes
            
            # Select the first wish
            pane.select_next()
            assert pane.selected_index == 1
            wish1_widget = app.query_one(f"#wish-{id(test_wishes[0])}")
            assert "selected" in wish1_widget.classes
            assert "selected" not in new_wish_option.classes
            
            # Select the second wish
            pane.select_next()
            assert pane.selected_index == 2
            wish2_widget = app.query_one(f"#wish-{id(test_wishes[1])}")
            assert "selected" in wish2_widget.classes
            assert "selected" not in wish1_widget.classes
            
            # Select the third wish
            pane.select_next()
            assert pane.selected_index == 3
            wish3_widget = app.query_one(f"#wish-{id(test_wishes[2])}")
            assert "selected" in wish3_widget.classes
            assert "selected" not in wish2_widget.classes
            
            # Try to go beyond the end, nothing should change
            pane.select_next()
            assert pane.selected_index == 3  # Still at the last wish
            assert "selected" in wish3_widget.classes
            
            # Go back to the second wish
            pane.select_previous()
            assert pane.selected_index == 2
            assert "selected" in wish2_widget.classes
            assert "selected" not in wish3_widget.classes
            
            # Go back to the first wish
            pane.select_previous()
            assert pane.selected_index == 1
            assert "selected" in wish1_widget.classes
            assert "selected" not in wish2_widget.classes
            
            # Go back to the NEW WISH option
            pane.select_previous()
            assert pane.selected_index == 0
            assert "selected" in new_wish_option.classes
            assert "selected" not in wish1_widget.classes
    
    @pytest.mark.asyncio
    async def test_wish_selected_message_with_mode(self):
        """Test that WishSelected messages include the correct mode."""
        # Create some test wishes
        test_wishes = [
            Wish.create("Wish 1"),
            Wish.create("Wish 2")
        ]
        
        app = WishSelectPaneTestApp(wishes=test_wishes)
        async with app.run_test() as pilot:
            pane = app.query_one(WishSelectPane)
            
            # Set up a message capture
            messages = []
            
            # Override the post_message method to capture WishSelected messages
            original_post_message = app.post_message
            
            def custom_post_message(message):
                if isinstance(message, WishSelected):
                    messages.append(message)
                return original_post_message(message)
            
            # Replace the post_message method
            app.post_message = custom_post_message
            
            # Initially, the NEW WISH option should be selected
            assert pane.selected_index == 0
            
            # Force an update to trigger the message
            pane.update_selection()
            await pilot.pause()
            
            # Check that a message was sent with NEW_WISH mode
            assert len(messages) == 1
            assert messages[0].wish is None
            assert messages[0].mode == WishMode.NEW_WISH
            
            # Select the first wish
            pane.select_next()
            await pilot.pause()
            
            # Check that a message was sent with WISH_HISTORY mode
            assert len(messages) == 2
            assert messages[1].wish is test_wishes[0]
            assert messages[1].mode == WishMode.WISH_HISTORY
            
            # Go back to the NEW WISH option
            pane.select_previous()
            await pilot.pause()
            
            # Check that a message was sent with NEW_WISH mode again
            assert len(messages) == 3
            assert messages[2].wish is None
            assert messages[2].mode == WishMode.NEW_WISH
