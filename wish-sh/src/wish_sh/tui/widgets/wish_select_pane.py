"""Wish Select Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal
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


class WishItem(Horizontal):
    """A widget representing a wish item with emoji and text in separate columns."""
    
    def __init__(self, wish, manager, is_selected=False):
        """Initialize the WishItem.
        
        Args:
            wish: The wish to display.
            manager: WishManager instance for getting emoji.
            is_selected: Whether this item is selected.
        """
        super().__init__()
        self.wish = wish
        self.manager = manager
        self.is_selected = is_selected
        self.add_class("wish-item")
        if is_selected:
            self.add_class("selected")
    
    def compose(self):
        """Compose the widget."""
        # Get emoji based on wish state
        emoji = self.manager._get_state_emoji(self.wish.state) if self.manager else "❓"
        
        # First column: emoji with fixed width
        yield Static(emoji, classes="emoji-cell fixed")
        
        # Second column: wish text
        yield Static(self.wish.wish, classes="text-cell")


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
                wish_item = WishItem(
                    wish=wish,
                    manager=self.manager,
                    is_selected=(i == self.selected_index)
                )
                wish_item.id = f"wish-{id(wish)}"
                yield wish_item  # Make sure this is wish_item, not wish_grid
    
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
