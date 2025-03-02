"""Log viewer screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static
import logging


class LogViewerScreen(Screen):
    """Log viewer screen for displaying command output logs."""

    BINDINGS = [
        Binding("j", "scroll_down", "Scroll Down", priority=True),
        Binding("down", "scroll_down", "Scroll Down", priority=True),
        Binding("k", "scroll_up", "Scroll Up", priority=True),
        Binding("up", "scroll_up", "Scroll Up", priority=True),
        Binding("ctrl+f", "page_down", "Page Down", priority=True),
        Binding("ctrl+b", "page_up", "Page Up", priority=True),
        Binding("<", "scroll_home", "Top", priority=True),
        Binding(">", "scroll_end", "Bottom", priority=True),
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("q", "dismiss", "Close", priority=True),
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
        
        # 最小限のロギング設定
        self.logger = logging.getLogger("wish_sh.tui.log_viewer")

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        with Container(id="log-viewer-dialog"):
            yield Static(self.title, id="log-viewer-title")
            yield Static(f"({self.line_count} lines total)", id="log-line-count")
            
            with ScrollableContainer(id="log-content-container"):
                # 各行を個別のStaticウィジェットとして表示
                content_lines = self.log_content.splitlines()
                
                # 最低でも30行のコンテンツを確保（スクロール可能な高さを保証）
                if len(content_lines) < 30:
                    content_lines.extend([""] * (30 - len(content_lines)))
                
                # 各行を個別のStaticとして追加
                for i, line in enumerate(content_lines):
                    yield Static(line, id=f"log-content-line-{i}", markup=False)
                    
            yield Static("Press ESC or q to close, j/k to scroll", id="log-viewer-footer")
    
    def action_scroll_down(self) -> None:
        """Scroll down one line."""
        container = self.query_one("#log-content-container")
        container.scroll_down()
        self.refresh()
    
    def action_scroll_up(self) -> None:
        """Scroll up one line."""
        container = self.query_one("#log-content-container")
        container.scroll_up()
        self.refresh()
    
    def action_page_down(self) -> None:
        """Scroll down one page."""
        container = self.query_one("#log-content-container")
        container.scroll_page_down()
        self.refresh()
    
    def action_page_up(self) -> None:
        """Scroll up one page."""
        container = self.query_one("#log-content-container")
        container.scroll_page_up()
        self.refresh()
    
    def action_scroll_home(self) -> None:
        """Scroll to the top."""
        container = self.query_one("#log-content-container")
        container.scroll_home()
        self.refresh()
    
    def action_scroll_end(self) -> None:
        """Scroll to the bottom."""
        container = self.query_one("#log-content-container")
        container.scroll_end()
        self.refresh()
    
    def action_dismiss(self) -> None:
        """Dismiss the screen."""
        self.app.pop_screen()
    
    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        # コンテナにフォーカスを当てる
        container = self.query_one("#log-content-container")
        self.set_focus(container)
    
    def on_show(self) -> None:
        """Event handler called when the screen is shown."""
        # コンテナにフォーカスを当てる
        self.focus()
        container = self.query_one("#log-content-container")
        self.set_focus(container)
    
    def on_enter(self) -> None:
        """Event handler called when the screen is entered."""
        # コンテナにフォーカスを当てる
        self.focus()
        container = self.query_one("#log-content-container")
        self.set_focus(container)
    
    def on_focus(self) -> None:
        """Event handler called when the screen gains focus."""
        # コンテナにフォーカスを当てる
        container = self.query_one("#log-content-container")
        self.set_focus(container)
    
    def on_key(self, event) -> None:
        """キーイベントを処理する"""
        # キーイベントをバインディングに任せる
        return False
    
    def on_idle(self) -> None:
        """アイドル時に呼び出され、フォーカス状態を監視"""
        container = self.query_one("#log-content-container")
        if not container.has_focus:
            self.set_focus(container)
