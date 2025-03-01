"""Tests for the WishSelectPane widget."""

import pytest
from textual.app import App, ComposeResult

from wish_sh.tui.widgets.wish_select_pane import WishSelectPane


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
            
            # Check that the pane has the expected content
            title = app.query_one("#wish-select-title")
            assert title is not None
            assert title.renderable == "Wish Select"
            
            # Check that the pane shows the "No wishes available" message
            content = app.query_one("#wish-select-content")
            assert content is not None
            assert content.renderable == "(No wishes available)"

    @pytest.mark.asyncio
    async def test_wish_select_pane_with_wishes(self):
        """Test that a WishSelectPane can display wishes."""
        # Create some test wishes
        test_wishes = ["Wish 1", "Wish 2", "Wish 3"]
        
        app = WishSelectPaneTestApp(wishes=test_wishes)
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            assert pane is not None
            
            # Check that the pane has the expected content
            title = app.query_one("#wish-select-title")
            assert title is not None
            
            # Check that the pane shows the wishes
            # We can't check the exact IDs since they're based on object IDs,
            # but we can check that there are the right number of Static widgets
            # and that they have the expected content
            statics = app.query("Static")
            assert len(statics) == len(test_wishes) + 1  # +1 for the title
            
            # The first Static is the title
            assert statics[0].renderable == "Wish Select"
            
            # The rest are the wishes
            for i, wish in enumerate(test_wishes):
                assert statics[i + 1].renderable == str(wish)

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
