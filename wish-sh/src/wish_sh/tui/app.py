"""Textual application for wish-sh TUI."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static

from wish_sh.tui.screens.main_screen import MainScreen


class WishTUIApp(App):
    """Textual application for wish-sh TUI."""

    TITLE = "wish-sh TUI"
    SUB_TITLE = "Your wish, our command"
    CSS_PATH = None  # We're using inline CSS for simplicity

    # Define key bindings
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("q", "confirm_quit", "Confirm Quit"),
        Binding("left", "focus_wish_select", "Focus Wish Select"),
        Binding("right", "focus_main", "Focus Main"),
        Binding("ctrl+up", "focus_main", "Focus Main"),
        Binding("ctrl+down", "focus_sub", "Focus Sub"),
    ]

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
        # Get the main screen
        main_screen = self.screen
        if hasattr(main_screen, "activate_pane"):
            main_screen.activate_pane("sub-pane")
        else:
            self.query_one("#sub-pane").focus()

    def action_confirm_quit(self) -> None:
        """Action to show quit confirmation dialog."""
        from wish_sh.tui.screens.quit_screen import QuitScreen
        self.push_screen(QuitScreen())
