"""Log viewer screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static


class LogViewerScreen(Screen):
    """Log viewer screen for displaying command output logs."""

    BINDINGS = [
        Binding("j", "scroll_down", "Scroll Down"),
        Binding("down", "scroll_down", "Scroll Down"),
        Binding("k", "scroll_up", "Scroll Up"),
        Binding("up", "scroll_up", "Scroll Up"),
        Binding("ctrl+f", "page_down", "Page Down"),
        Binding("ctrl+b", "page_up", "Page Up"),
        Binding("<", "scroll_home", "Top"),
        Binding(">", "scroll_end", "Bottom"),
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    def __init__(self, log_content, title, *args, **kwargs):
        """Initialize the LogViewerScreen.
        
        Args:
            log_content: The log content to display.
            title: The title of the log viewer.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.log_content = log_content
        self.title = title
        self.line_count = len(log_content.splitlines()) if log_content else 0

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        with Container(id="log-viewer-dialog"):
            yield Static(self.title, id="log-viewer-title")
            yield Static(f"({self.line_count} lines total)", id="log-line-count")
            yield Static(self.log_content, id="log-content", markup=False)
            yield Static("Press ESC or q to close", id="log-viewer-footer")
    
    def action_scroll_down(self) -> None:
        """Scroll down one line."""
        content = self.query_one("#log-content")
        content.scroll_down()
    
    def action_scroll_up(self) -> None:
        """Scroll up one line."""
        content = self.query_one("#log-content")
        content.scroll_up()
    
    def action_page_down(self) -> None:
        """Scroll down one page."""
        content = self.query_one("#log-content")
        for _ in range(10):  # 10行分スクロール
            content.scroll_down()
    
    def action_page_up(self) -> None:
        """Scroll up one page."""
        content = self.query_one("#log-content")
        for _ in range(10):  # 10行分スクロール
            content.scroll_up()
    
    def action_scroll_home(self) -> None:
        """Scroll to the top."""
        content = self.query_one("#log-content")
        content.scroll_home()
    
    def action_scroll_end(self) -> None:
        """Scroll to the bottom."""
        content = self.query_one("#log-content")
        content.scroll_end()
    
    def action_dismiss(self) -> None:
        """Dismiss the screen."""
        self.app.pop_screen()
