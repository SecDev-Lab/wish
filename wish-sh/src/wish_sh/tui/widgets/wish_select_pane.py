"""Wish Select Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static

from wish_sh.tui.modes import WishMode
from wish_sh.tui.widgets.base_pane import BasePane
from wish_sh.wish_manager import WishManager


class WishSelected(Message):
    """Message sent when a wish is selected."""

    def __init__(self, wish, mode):
        """Initialize the message.
        
        Args:
            wish: The selected wish.
            mode: The current mode (WishMode).
        """
        self.wish = wish
        self.mode = mode
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
        # Start with NEW WISH selected by default
        self.selected_index = 0
        self.current_mode = WishMode.NEW_WISH

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # Add NEW WISH option at the top
        new_wish_emoji = "✨"  # Sparkles emoji as a "good emoji"
        new_wish_static = Static(f"{new_wish_emoji} NEW WISH", id="new-wish-option", classes="wish-item")
        
        # Select NEW WISH by default
        if self.selected_index == 0:
            new_wish_static.add_class("selected")
            
        yield new_wish_static
        
        # Add existing wishes
        if not self.wishes:
            yield Static("(No wishes available)", id="wish-select-content", markup=False)
        else:
            for i, wish in enumerate(self.wishes):
                # Get emoji based on wish state
                emoji = self.manager._get_state_emoji(wish.state) if self.manager else "❓"
                
                # Create a single Static widget with fixed spacing (reduced from 3 to 2 spaces)
                static = Static(f"{emoji} {wish.wish}", id=f"wish-{id(wish)}", classes="wish-item")
                
                # Adjust index to account for NEW WISH option
                if i + 1 == self.selected_index:
                    static.add_class("selected")
                
                yield static
    
    def on_key(self, event) -> None:
        """Handle key events."""
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
        # +1 for NEW WISH option
        if self.selected_index < len(self.wishes):
            self.selected_index += 1
            self.update_selection()
    
    def update_selection(self) -> None:
        """Update the selection state and post a message."""
        # Reset all selection states
        try:
            # Reset NEW WISH option
            new_wish_widget = self.query_one("#new-wish-option")
            new_wish_widget.remove_class("selected")
        except Exception:
            # Widget might not be found if the UI is being rebuilt
            pass
            
        # Reset all wish selection states
        for i in range(len(self.wishes)):
            wish_id = f"wish-{id(self.wishes[i])}"
            try:
                widget = self.query_one(f"#{wish_id}")
                widget.remove_class("selected")
            except Exception:
                # Widget might not be found if the UI is being rebuilt
                pass
        
        # Determine current mode and selected wish
        if self.selected_index == 0:
            # NEW WISH mode
            self.current_mode = WishMode.NEW_WISH
            selected_wish = None
            try:
                widget = self.query_one("#new-wish-option")
                widget.add_class("selected")
            except Exception:
                # Widget might not be found if the UI is being rebuilt
                pass
        else:
            # WISH HISTORY mode
            self.current_mode = WishMode.WISH_HISTORY
            wish_index = self.selected_index - 1  # Adjust for NEW WISH option
            selected_wish = self.wishes[wish_index]
            try:
                wish_id = f"wish-{id(selected_wish)}"
                widget = self.query_one(f"#{wish_id}")
                widget.add_class("selected")
            except Exception:
                # Widget might not be found if the UI is being rebuilt
                pass
        
        # Post a message with the selected wish and current mode
        self.post_message(WishSelected(selected_wish, self.current_mode))
