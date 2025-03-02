"""Main screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen

from wish_sh.logging import setup_logger
from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager
from wish_sh.tui.modes import WishMode
from wish_sh.tui.widgets.help_pane import HelpPane
from wish_sh.tui.widgets.main_pane import MainPane, CommandSelected
from wish_sh.tui.widgets.sub_pane import SubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane, WishSelected


class ActivatePane(Message):
    """Message sent to request activation of a specific pane."""

    def __init__(self, pane_id: str):
        """Initialize the message.
        
        Args:
            pane_id: The ID of the pane to activate.
        """
        self.pane_id = pane_id
        super().__init__()


class MainScreen(Screen):
    """Main screen for the wish-sh TUI application."""
    
    def __init__(self, *args, wish_manager=None, **kwargs):
        """Initialize the MainScreen."""
        super().__init__(*args, **kwargs)
        # Set up logger
        self.logger = setup_logger("wish_sh.tui.MainScreen")
        
        # Initialize with dependency injection
        self.settings = Settings()
        self.manager = wish_manager or WishManager(self.settings)
        # Load past wishes
        self.wishes = self.manager.load_wishes()
        # Initialize with NEW_WISH mode by default
        self.current_mode = WishMode.NEW_WISH

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
        
        # Initialize with NEW_WISH mode
        self.set_mode(WishMode.NEW_WISH)
    
    def on_key(self, event) -> None:
        """Handle key events."""
        # Log key events at debug level
        self.logger.debug(f"Key event: {event.key}")
        self.logger.debug(f"Active pane: wish_select={self.wish_select.has_class('active-pane')}, "
                         f"main_pane={self.main_pane.has_class('active-pane')}, "
                         f"sub_pane={self.sub_pane.has_class('active-pane')}")
        self.logger.debug(f"Current mode: {self.current_mode}")
        
        # Log Ctrl+Down key events
        if event.key in ("ctrl+down", "ctrl+arrow_down", "down+ctrl"):
            self.logger.debug(f"Ctrl+Down key detected: {event.key}")
        
        # Handle up/down keys when Wish Select pane is active
        if self.wish_select.has_class("active-pane"):
            if event.key in ("up", "arrow_up"):
                self.logger.debug("Passing up key to wish_select")
                self.wish_select.select_previous()
                return True  # Consume event
            elif event.key in ("down", "arrow_down"):
                self.logger.debug("Passing down key to wish_select")
                self.wish_select.select_next()
                return True  # Consume event
        
        # Handle up/down keys when Main pane is active and in WISH_HISTORY mode
        if self.main_pane.has_class("active-pane") and self.current_mode == WishMode.WISH_HISTORY:
            if event.key in ("up", "arrow_up", "down", "arrow_down"):
                self.logger.debug("Passing up/down key to main_pane")
                # Pass the key event to the main pane
                if self.main_pane.on_key(event):
                    return True  # Consume event if the main pane handled it
                else:
                    self.logger.debug("main_pane did not handle the key event")
        
        # Handle o/e keys when Sub pane is active and in WISH_HISTORY mode
        if self.sub_pane.has_class("active-pane") and self.current_mode == WishMode.WISH_HISTORY:
            if event.key in ("o", "e"):
                self.logger.debug(f"Passing {event.key} key to sub_pane")
                # Pass the key event to the sub pane
                if self.sub_pane.on_key(event):
                    return True  # Consume event if the sub pane handled it
                else:
                    self.logger.debug(f"sub_pane did not handle the {event.key} key event")
        
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
    
    def set_mode(self, mode: WishMode, wish=None) -> None:
        """Set the current mode and update panes accordingly.
        
        Args:
            mode: The mode to set.
            wish: The wish to display (for WISH_HISTORY mode).
        """
        self.current_mode = mode
        
        if mode == WishMode.NEW_WISH:
            # Update panes for NEW WISH mode
            self.main_pane.update_for_new_wish_mode()
            self.sub_pane.update_for_new_wish_mode()
        else:
            # Update panes for WISH HISTORY mode
            self.main_pane.update_wish(wish)
            
            # Reset Sub pane to default state for WISH HISTORY mode
            content_widget = self.sub_pane.query_one("#sub-pane-content")
            content_widget.update("(Select a command to view details)")
    
    def on_wish_selected(self, event: WishSelected) -> None:
        """Handle wish selection events."""
        self.set_mode(event.mode, event.wish)
    
    def on_command_selected(self, event: CommandSelected) -> None:
        """Handle command selection events."""
        # Update the sub pane with command output but keep focus on main pane
        self.sub_pane.update_command_output(event.command_result)
        # Do not activate the sub pane to keep focus on main pane
        # self.activate_pane("sub-pane")
        
    def on_activate_pane(self, event: ActivatePane) -> None:
        """Handle pane activation requests."""
        self.activate_pane(event.pane_id)
