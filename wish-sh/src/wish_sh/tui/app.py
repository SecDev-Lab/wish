"""Textual application for wish-sh TUI."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static

from wish_sh.logging import setup_logger
from wish_sh.tui.screens.main_screen import MainScreen


class WishTUIApp(App):
    """Textual application for wish-sh TUI."""

    TITLE = "wish-sh TUI"
    SUB_TITLE = "Your wish, our command"
    CSS_PATH = "wish_tui.css"  # Use external CSS file

    # Define key bindings
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("q", "confirm_quit", "Confirm Quit"),
        Binding("left", "focus_wish_select", "Focus Wish Select"),
        Binding("ctrl+h", "focus_wish_select", "Focus Wish Select"),
        Binding("right", "focus_main", "Focus Main"),
        Binding("ctrl+l", "focus_main", "Focus Main"),
        Binding("ctrl+up", "focus_main", "Focus Main"),
        Binding("ctrl+k", "focus_main", "Focus Main"),
        Binding("ctrl+down", "focus_sub", "Focus Sub"),
        Binding("ctrl+j", "focus_sub", "Focus Sub"),
        Binding("j", "scroll_down_line", "Scroll Down"),
        Binding("down", "scroll_down_line", "Scroll Down"),
        Binding("k", "scroll_up_line", "Scroll Up"),
        Binding("up", "scroll_up_line", "Scroll Up"),
        Binding("ctrl+f", "scroll_page_down", "Page Down"),
        Binding("ctrl+b", "scroll_page_up", "Page Up"),
        Binding(">", "scroll_end", "Bottom"),
        Binding("<", "scroll_home", "Top"),
        Binding("enter", "activate_selected", "Activate Selected"),
        Binding("space", "activate_selected", "Activate Selected"),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super().__init__(*args, **kwargs)
        self.logger = setup_logger("wish_sh.tui.WishTUIApp")

    def compose(self) -> ComposeResult:
        """Compose the application."""
        # We need to yield something here, even though we're using push_screen
        # This is a placeholder that will be replaced by the pushed screen
        yield Static("")

    def on_mount(self) -> None:
        """Event handler called when the app is mounted."""
        # Push the main screen
        self.push_screen(MainScreen())

    def action_focus_wish_select(self) -> None:
        """Action to focus the wish select pane."""
        # Get the main screen
        main_screen = self.screen
        if hasattr(main_screen, "activate_pane"):
            main_screen.activate_pane("wish-select")
        else:
            self.query_one("#wish-select").focus()

    def action_focus_main(self) -> None:
        """Action to focus the main pane."""
        # Get the main screen
        main_screen = self.screen
        if hasattr(main_screen, "activate_pane"):
            main_screen.activate_pane("main-pane")
        else:
            self.query_one("#main-pane").focus()

    def action_focus_sub(self) -> None:
        """Action to focus the sub pane."""
        self.logger.debug("action_focus_sub called")
        
        # Get the main screen
        main_screen = self.screen
        if hasattr(main_screen, "activate_pane"):
            self.logger.debug("Calling main_screen.activate_pane('sub-pane')")
            main_screen.activate_pane("sub-pane")
        else:
            self.logger.debug("Calling self.query_one('#sub-pane').focus()")
            self.query_one("#sub-pane").focus()

    def action_confirm_quit(self) -> None:
        """Action to show quit confirmation dialog."""
        from wish_sh.tui.screens.quit_screen import QuitScreen
        self.push_screen(QuitScreen())
    
    def action_scroll_up_line(self) -> None:
        """Scroll up one line or select previous item in the active pane."""
        active_pane = self.get_active_pane()
        if not active_pane:
            return
            
        if active_pane.id == "sub-pane":
            # Scroll if it's a Sub pane
            content = active_pane.query_one("#sub-pane-content")
            content.scroll_up()
        elif active_pane.id == "wish-select":
            # Select previous item if it's a Wish Select pane
            active_pane.select_previous()
        elif active_pane.id == "main-pane":
            # Select previous command if it's a Main pane
            active_pane.select_previous_command()
    
    def action_scroll_down_line(self) -> None:
        """Scroll down one line or select next item in the active pane."""
        active_pane = self.get_active_pane()
        if not active_pane:
            return
            
        if active_pane.id == "sub-pane":
            # Scroll if it's a Sub pane
            content = active_pane.query_one("#sub-pane-content")
            content.scroll_down()
        elif active_pane.id == "wish-select":
            # Select next item if it's a Wish Select pane
            active_pane.select_next()
        elif active_pane.id == "main-pane":
            # Select next command if it's a Main pane
            active_pane.select_next_command()
    
    def action_scroll_page_up(self) -> None:
        """Page up in the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            # Scroll up one page
            content.scroll_page_up()
    
    def action_scroll_page_down(self) -> None:
        """Page down in the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            # Scroll down one page
            content.scroll_page_down()
    
    def action_scroll_home(self) -> None:
        """Scroll to the top of the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            content.scroll_home()
    
    def action_scroll_end(self) -> None:
        """Scroll to the bottom of the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            content.scroll_end()
    
    def get_active_pane(self):
        """Get the currently active pane."""
        main_screen = self.screen
        
        # wish_select is common
        if hasattr(main_screen, "wish_select") and main_screen.wish_select.has_class("active-pane"):
            return main_screen.wish_select
        
        # Reference appropriate main_pane and sub_pane according to the current mode
        if hasattr(main_screen, "current_mode"):
            from wish_sh.tui.modes import WishMode
            
            if main_screen.current_mode == WishMode.WISH_HISTORY:
                # In WISH_HISTORY mode
                if hasattr(main_screen, "wish_history_main_pane") and main_screen.wish_history_main_pane.has_class("active-pane"):
                    return main_screen.wish_history_main_pane
                elif hasattr(main_screen, "wish_history_sub_pane") and main_screen.wish_history_sub_pane.has_class("active-pane"):
                    return main_screen.wish_history_sub_pane
            else:
                # In NEW_WISH mode
                if hasattr(main_screen, "new_wish_main_pane") and main_screen.new_wish_main_pane.has_class("active-pane"):
                    return main_screen.new_wish_main_pane
                elif hasattr(main_screen, "new_wish_sub_pane") and main_screen.new_wish_sub_pane.has_class("active-pane"):
                    return main_screen.new_wish_sub_pane
        
        return None
    
    def action_activate_selected(self) -> None:
        """Activate the selected item in the active pane."""
        self.logger.debug("action_activate_selected called")
        active_pane = self.get_active_pane()
        
        if active_pane and active_pane.id == "wish-select":
            # If Wish Select Pane is active, activate Main Pane
            self.logger.debug("Wish Select Pane is active, activating Main Pane")
            self.action_focus_main()
        elif active_pane and active_pane.id == "main-pane":
            # If Main Pane is active, activate Sub Pane
            self.logger.debug("Main Pane is active, activating Sub Pane")
            self.action_focus_sub()
    
    def on_key(self, event) -> None:
        """Monitor key events for the entire application."""
        # Log key events at debug level
        self.logger.debug(f"App received key: {event.key}")
        
        # Handle Ctrl+Down key for debugging
        if event.key in ("ctrl+down", "ctrl+arrow_down", "down+ctrl"):
            self.logger.debug(f"Ctrl+Down key detected: {event.key}")
        
        # Handle LogViewerScreen key events
        from wish_sh.tui.screens.log_viewer_screen import LogViewerScreen
        if isinstance(self.screen, LogViewerScreen):
            self.logger.debug(f"Key event for LogViewerScreen: {event.key}")
            result = self.screen.on_key(event)
            self.logger.debug(f"LogViewerScreen on_key result: {result}")
            return result
        
        # Normal key event processing
        return False
