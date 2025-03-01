"""Quit confirmation screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class QuitScreen(ModalScreen):
    """Confirmation dialog for quitting the application."""

    # CSS moved to external file: wish_tui.css

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        with Middle():
            with Center():
                with Static(classes="quit-dialog"):
                    yield Label("Are you sure you want to quit?")
                    with Center():
                        yield Button("Yes", id="yes", variant="primary")
                        yield Button("No", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "yes":
            self.app.exit()
        else:
            self.app.pop_screen()
