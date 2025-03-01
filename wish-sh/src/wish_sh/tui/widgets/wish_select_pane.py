"""Wish Select Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane
from wish_sh.wish_manager import WishManager


class WishSelected(Message):
    """Message sent when a wish is selected."""

    def __init__(self, wish):
        """Initialize the message.
        
        Args:
            wish: The selected wish.
        """
        self.wish = wish
        super().__init__()


class WishSelectPane(BasePane):
    """A pane for selecting wishes."""

    # CSS moved to external file: wish_tui.css

    def __init__(self, wishes=None, manager=None, *args, **kwargs):
        """Initialize the WishSelectPane.
        
        Args:
            wishes: List of wishes to display.
            manager: WishManager instance for formatting wishes.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.wishes = wishes or []
        self.manager = manager
        self.selected_index = 0 if self.wishes else -1

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Wish Select", id="wish-select-title", markup=False)
        
        if not self.wishes:
            yield Static("(No wishes available)", id="wish-select-content", markup=False)
        else:
            for i, wish in enumerate(self.wishes):
                # Get emoji based on wish state
                emoji = self.manager._get_state_emoji(wish.state) if self.manager else "❓"
                
                # Create a single Static widget with fixed spacing (reduced from 3 to 2 spaces)
                static = Static(f"{emoji} {wish.wish}", id=f"wish-{id(wish)}", classes="wish-item")
                
                if i == self.selected_index:
                    static.add_class("selected")
                
                yield static
    
    def on_key(self, event) -> None:
        """Handle key events."""
        if not self.wishes:
            return False
        
        if event.key in ("up", "arrow_up"):
            self.select_previous()
            return True
        elif event.key in ("down", "arrow_down"):
            self.select_next()
            return True
        
        return False
    
    def select_previous(self) -> None:
        """Select the previous wish."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self.update_selection()
    
    def select_next(self) -> None:
        """Select the next wish."""
        if self.selected_index < len(self.wishes) - 1:
            self.selected_index += 1
            self.update_selection()
    
    def update_selection(self) -> None:
        """Update the selection state and post a message."""
        # Reset all wish selection states
        for i in range(len(self.wishes)):
            wish_id = f"wish-{id(self.wishes[i])}"
            try:
                widget = self.query_one(f"#{wish_id}")
                widget.remove_class("selected")
            except Exception:
                # Widget might not be found if the UI is being rebuilt
                pass
        
        # Add selected class to the currently selected wish
        if self.selected_index >= 0:
            wish_id = f"wish-{id(self.wishes[self.selected_index])}"
            try:
                widget = self.query_one(f"#{wish_id}")
                widget.add_class("selected")
                
                # Post a message that a wish was selected
                self.post_message(WishSelected(self.wishes[self.selected_index]))
            except Exception:
                # Widget might not be found if the UI is being rebuilt
                pass
