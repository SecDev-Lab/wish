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

    DEFAULT_CSS = """
    WishSelectPane {
        width: 30;
        height: 100%;
    }
    
    WishSelectPane Static.selected {
        background: $accent-darken-2;
        color: $text-accent;
    }
    """

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
            for i, wish in enumerate(self.wishes, 1):
                # Use a simple representation to avoid markup issues
                static = Static(f"[{i}] {wish.wish}", id=f"wish-{id(wish)}", markup=False)
                if i - 1 == self.selected_index:
                    static.add_class("selected")
                yield static
    
    def on_key(self, event) -> None:
        """Handle key events."""
        if not self.wishes:
            return False

        # デバッグ情報を表示
        self.log(f"WishSelectPane received key: {event.key}")
        
        if event.key in ("up", "arrow_up"):
            self.log("Processing up key")
            self.select_previous()
            return True
        elif event.key in ("down", "arrow_down"):
            self.log("Processing down key")
            self.select_next()
            return True
        
        return False
    
    # Textualの標準キーイベントハンドラを追加（異なる命名規則を試す）
    def key_up(self) -> None:
        """Handle up key press."""
        self.log("key_up called")
        if self.wishes:
            self.select_previous()
    
    def key_down(self) -> None:
        """Handle down key press."""
        self.log("key_down called")
        if self.wishes:
            self.select_next()
            
    # 別の命名規則も試す
    def on_press_up(self) -> None:
        """Handle up key press."""
        self.log("on_press_up called")
        if self.wishes:
            self.select_previous()
    
    def on_press_down(self) -> None:
        """Handle down key press."""
        self.log("on_press_down called")
        if self.wishes:
            self.select_next()
    
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
            widget = self.query_one(f"#{wish_id}")
            widget.remove_class("selected")
        
        # Add selected class to the currently selected wish
        if self.selected_index >= 0:
            wish_id = f"wish-{id(self.wishes[self.selected_index])}"
            widget = self.query_one(f"#{wish_id}")
            widget.add_class("selected")
            
            # Post a message that a wish was selected
            self.post_message(WishSelected(self.wishes[self.selected_index]))
