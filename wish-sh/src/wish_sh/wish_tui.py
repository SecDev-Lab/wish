from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from wish_models import Wish, WishState


class WishInput(Screen):
    """Screen for inputting a wish."""

    def compose(self) -> ComposeResult:
        """Compose the wish input screen."""
        yield Header(show_clock=True)
        yield Container(
            Label("wish✨️", id="wish-prompt", markup=False),
            Input(placeholder="Enter your wish here...", id="wish-input"),
            id="wish-container",
        )
        yield Footer()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        wish_text = event.value.strip()
        if wish_text:
            # Create a new wish
            wish = Wish.create(wish_text)
            wish.state = WishState.DOING
            
            # Generate mock commands (in a real app, this would call an LLM)
            commands = [
                f"echo 'Executing wish: {wish_text}'",
                f"echo 'Processing {wish_text}' && ls -la"
            ]
            
            # Switch to command suggestion screen
            self.app.push_screen(CommandSuggestion(wish, commands))


class CommandSuggestion(Screen):
    """Screen for suggesting commands."""

    def __init__(self, wish: Wish, commands: list[str]) -> None:
        """Initialize the command suggestion screen."""
        super().__init__()
        self.wish = wish
        self.commands = commands

    def compose(self) -> ComposeResult:
        """Compose the command suggestion screen."""
        yield Header(show_clock=True)
        yield Vertical(
            Label(f"Wish: {self.wish.wish}", id="wish-text", markup=False),
            Static("Do you want to execute these commands?", id="confirmation-text", markup=False),
            *(Label(f"[{i+1}] {cmd}", id=f"command-{i+1}", markup=False) for i, cmd in enumerate(self.commands)),
            Container(
                Button("Yes", id="yes-button", variant="success"),
                Button("No", id="no-button", variant="error"),
                id="button-container",
            ),
            id="command-container",
        )
        yield Footer()

    @on(Button.Pressed, "#yes-button")
    def on_yes_button_pressed(self) -> None:
        """Handle yes button press."""
        # In a real app, this would execute the commands
        self.app.push_screen(CommandExecutionScreen(self.wish, self.commands))

    @on(Button.Pressed, "#no-button")
    def on_no_button_pressed(self) -> None:
        """Handle no button press."""
        # Go back to wish input screen
        self.app.pop_screen()


class CommandExecutionScreen(Screen):
    """Screen for showing command execution."""

    def __init__(self, wish: Wish, commands: list[str]) -> None:
        """Initialize the command execution screen."""
        super().__init__()
        self.wish = wish
        self.commands = commands

    def compose(self) -> ComposeResult:
        """Compose the command execution screen."""
        yield Header(show_clock=True)
        yield Vertical(
            Label(f"Wish: {self.wish.wish}", id="wish-text", markup=False),
            Static("Commands would be executed here.", id="execution-text", markup=False),
            *(Label(f"[{i+1}] {cmd}", id=f"command-{i+1}", markup=False) for i, cmd in enumerate(self.commands)),
            Button("Back to Wish Input", id="back-button"),
            id="execution-container",
        )
        yield Footer()

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        """Handle back button press."""
        # Go back to wish input screen (pop twice to skip command suggestion)
        self.app.pop_screen()
        self.app.pop_screen()


class WishApp(App):
    """The main Wish TUI application."""

    CSS = """
    #wish-prompt {
        margin: 1 0;
        text-align: center;
        width: 100%;
        color: yellow;
        text-style: bold;
    }

    #wish-container {
        align: center middle;
        width: 80%;
        height: 10;
    }

    #wish-input {
        width: 100%;
    }

    #command-container {
        align: center middle;
        width: 80%;
    }

    #wish-text {
        margin: 1 0;
        text-align: center;
        width: 100%;
    }

    #confirmation-text {
        margin: 1 0;
        text-align: center;
        width: 100%;
        color: yellow;
    }

    #button-container {
        margin: 1 0;
        width: 100%;
        height: 3;
        align-horizontal: center;
    }

    Button {
        margin: 0 1;
    }

    #execution-container {
        align: center middle;
        width: 80%;
    }

    #execution-text {
        margin: 1 0;
        text-align: center;
        width: 100%;
        color: green;
    }

    #back-button {
        margin: 1 0;
    }
    """

    TITLE = "Wish Shell"
    SCREENS = {"wish_input": WishInput}
    BINDINGS = [("escape", "quit", "Quit")]

    def on_mount(self) -> None:
        """Handle app mount event."""
        self.push_screen("wish_input")


def main() -> None:
    """Run the Wish TUI application."""
    app = WishApp()
    app.run()


if __name__ == "__main__":
    main()
