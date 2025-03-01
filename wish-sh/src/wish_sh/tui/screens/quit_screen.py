"""Quit confirmation screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class QuitScreen(ModalScreen):
    """Confirmation dialog for quitting the application."""

    DEFAULT_CSS = """
    QuitScreen {
        align: center middle;
    }

    .quit-dialog {
        background: $surface;
        padding: 1 2;
        border: solid $primary;
        width: 40;
    }

    .quit-dialog Button {
        margin: 1 1 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        with Middle():
            with Center():
                with Static(classes="quit-dialog"):
                    yield Label("本当に終了しますか？")
                    with Center():
                        yield Button("はい", id="yes", variant="primary")
                        yield Button("いいえ", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "yes":
            self.app.exit()
        else:
            self.app.pop_screen()
