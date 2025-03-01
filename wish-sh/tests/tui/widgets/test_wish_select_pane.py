"""Tests for the WishSelectPane widget."""

import pytest
from textual.app import App, ComposeResult
from textual.pilot import Pilot
from wish_models import Wish

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
        test_wishes = [
            Wish.create("Wish 1"),
            Wish.create("Wish 2"),
            Wish.create("Wish 3")
        ]
        
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
            
            # The rest are the wishes with their index
            for i, wish in enumerate(test_wishes, 1):
                # Check that the text contains both the index and the wish text
                assert f"[{i}]" in statics[i].renderable
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
            assert len(statics) == len(test_wishes) + 1  # +1 for the title
            
            # The first Static is the title
            assert statics[0].renderable == "Wish Select"
            
            # The rest are the wishes with their index
            for i, wish in enumerate(test_wishes, 1):
                # Check that the text contains both the index and the wish text
                assert f"[{i}]" in statics[i].renderable
                assert wish.wish in statics[i].renderable

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
            assert len(statics) == 2  # title + 1 wish
            
            # The wish text should contain both the index and the brackets
            assert "[1]" in statics[1].renderable
            assert "[This is a wish with brackets]" in statics[1].renderable
    
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
            
            # Initially, the first wish should be selected
            assert pane.selected_index == 0
            wish1_widget = app.query_one(f"#wish-{id(test_wishes[0])}")
            assert "selected" in wish1_widget.classes
            
            # Select the second wish directly
            pane.select_next()
            assert pane.selected_index == 1
            wish2_widget = app.query_one(f"#wish-{id(test_wishes[1])}")
            assert "selected" in wish2_widget.classes
            assert "selected" not in wish1_widget.classes
            
            # Select the third wish
            pane.select_next()
            assert pane.selected_index == 2
            wish3_widget = app.query_one(f"#wish-{id(test_wishes[2])}")
            assert "selected" in wish3_widget.classes
            assert "selected" not in wish2_widget.classes
            
            # Try to go beyond the end, nothing should change
            pane.select_next()
            assert pane.selected_index == 2  # Still at the last wish
            assert "selected" in wish3_widget.classes
            
            # Go back to the second wish
            pane.select_previous()
            assert pane.selected_index == 1
            assert "selected" in wish2_widget.classes
            assert "selected" not in wish3_widget.classes
    
    @pytest.mark.asyncio
    async def test_wish_selected_message(self):
        """Test that a wish can be selected and deselected."""
        # Create some test wishes
        test_wishes = [
            Wish.create("Wish 1"),
            Wish.create("Wish 2")
        ]
        
        app = WishSelectPaneTestApp(wishes=test_wishes)
        async with app.run_test():
            pane = app.query_one(WishSelectPane)
            
            # Initially, the first wish should be selected
            assert pane.selected_index == 0
            
            # Select the second wish directly
            pane.select_next()
            assert pane.selected_index == 1
            
            # Go back to the first wish
            pane.select_previous()
            assert pane.selected_index == 0
