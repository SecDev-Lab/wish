"""Main screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen

from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager
from wish_sh.tui.widgets.help_pane import HelpPane
from wish_sh.tui.widgets.main_pane import MainPane, CommandSelected
from wish_sh.tui.widgets.sub_pane import SubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane, WishSelected


class MainScreen(Screen):
    """Main screen for the wish-sh TUI application."""
    
    def __init__(self, *args, wish_manager=None, **kwargs):
        """Initialize the MainScreen."""
        super().__init__(*args, **kwargs)
        # Initialize with dependency injection
        self.settings = Settings()
        self.manager = wish_manager or WishManager(self.settings)
        # Load past wishes
        self.wishes = self.manager.load_wishes()

    # CSS moved to external file: wish_tui.css

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        # Create the main layout
        self.wish_select = WishSelectPane(wishes=self.wishes, manager=self.manager, id="wish-select")
        self.main_pane = MainPane(id="main-pane")
        self.sub_pane = SubPane(id="sub-pane")
        self.help_pane = HelpPane(id="help-pane")

        # Yield the widgets in the desired order
        yield self.wish_select
        yield self.main_pane
        yield self.sub_pane
        yield self.help_pane

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        # Set initial focus to the main pane
        self.main_pane.focus()
        
        # Set initial active state
        self.wish_select.set_active(False)
        self.main_pane.set_active(True)
        self.sub_pane.set_active(False)
        
        # Update help text for initial active pane
        self.help_pane.update_help("main-pane")
        
        # If there are wishes, select the first one and update the main pane
        if self.wishes:
            self.main_pane.update_wish(self.wishes[0])
    
    def on_key(self, event) -> None:
        """Handle key events."""
        # Handle up/down keys when Wish Select pane is active
        if self.wish_select.has_class("active-pane"):
            if event.key in ("up", "arrow_up"):
                self.wish_select.select_previous()
                return True  # Consume event
            elif event.key in ("down", "arrow_down"):
                self.wish_select.select_next()
                return True  # Consume event
        
        # Navigate between panes with arrow keys
        if event.key in ("left", "arrow_left"):
            self.activate_pane("wish-select")
            return True  # Consume event
        elif event.key in ("right", "arrow_right"):
            self.activate_pane("main-pane")
            return True  # Consume event
        # Use Ctrl+arrow keys for vertical navigation
        elif event.key in ("ctrl+up", "ctrl+arrow_up", "up+ctrl"):
            self.activate_pane("main-pane")
            return True  # Consume event
        elif event.key in ("ctrl+down", "ctrl+arrow_down", "down+ctrl"):
            self.activate_pane("sub-pane")
            return True  # Consume event
    
    def activate_pane(self, pane_id: str) -> None:
        """Activate the specified pane."""
        # Deactivate all panes
        self.wish_select.set_active(False)
        self.main_pane.set_active(False)
        self.sub_pane.set_active(False)
        
        # Activate the specified pane
        if pane_id == "wish-select":
            self.wish_select.set_active(True)
            self.wish_select.focus()
        elif pane_id == "main-pane":
            self.main_pane.set_active(True)
            self.main_pane.focus()
        elif pane_id == "sub-pane":
            self.sub_pane.set_active(True)
            self.sub_pane.focus()
        
        # Update help text based on active pane
        self.help_pane.update_help(pane_id)
    
    def on_wish_selected(self, event: WishSelected) -> None:
        """Handle wish selection events."""
        self.main_pane.update_wish(event.wish)
    
    def on_command_selected(self, event: CommandSelected) -> None:
        """Handle command selection events."""
        self.sub_pane.update_command_output(event.command_result)
        # Activate the sub pane to show the command output
        self.activate_pane("sub-pane")
