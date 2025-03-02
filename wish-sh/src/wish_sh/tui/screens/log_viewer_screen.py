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
        # デバッグ用のロガーを設定
        self.logger = logging.getLogger("wish_sh.tui.log_viewer")
        self.logger.setLevel(logging.DEBUG)
        # ファイルハンドラーを追加
        handler = logging.FileHandler("/tmp/wish_sh_log_viewer.log")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.debug("LogViewerScreen initialized")

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        self.logger.debug("Composing LogViewerScreen")
        with Container(id="log-viewer-dialog"):
            yield Static(self.title, id="log-viewer-title")
            yield Static(f"({self.line_count} lines total)", id="log-line-count")
            # ScrollableContainer を使用
            with ScrollableContainer(id="log-content-container"):
                # コンテンツの高さを強制的に大きくするために、各行を個別のStaticとして追加
                content_lines = self.log_content.splitlines()
                # 最低でも30行のコンテンツを確保
                if len(content_lines) < 30:
                    content_lines.extend([""] * (30 - len(content_lines)))
                
                # 各行を個別のStaticとして追加
                for i, line in enumerate(content_lines):
                    yield Static(line, id=f"log-content-line-{i}", markup=False)
            yield Static("Press ESC or q to close, j/k to scroll", id="log-viewer-footer")
    
    def action_scroll_down(self) -> None:
        """Scroll down one line."""
        self.logger.debug("action_scroll_down called")
        container = self.query_one("#log-content-container")
        before_y = container.scroll_y
        self.logger.debug(f"BEFORE scroll_down: container.scroll_y={before_y}")
        
        # スクロール処理をシンプルに（引数なし）
        container.scroll_down()
        
        # 強制的に再描画
        self.refresh()
        
        after_y = container.scroll_y
        self.logger.debug(f"AFTER scroll_down: container.scroll_y={after_y}, delta={after_y - before_y}")
    
    def action_scroll_up(self) -> None:
        """Scroll up one line."""
        self.logger.debug("action_scroll_up called")
        container = self.query_one("#log-content-container")
        before_y = container.scroll_y
        self.logger.debug(f"BEFORE scroll_up: container.scroll_y={before_y}")
        
        # スクロール処理をシンプルに（引数なし）
        container.scroll_up()
        
        # 強制的に再描画
        self.refresh()
        
        after_y = container.scroll_y
        self.logger.debug(f"AFTER scroll_up: container.scroll_y={after_y}, delta={after_y - before_y}")
    
    def action_page_down(self) -> None:
        """Scroll down one page."""
        self.logger.debug("action_page_down called")
        container = self.query_one("#log-content-container")
        before_y = container.scroll_y
        self.logger.debug(f"BEFORE page_down: container.scroll_y={before_y}")
        
        # 10行分スクロール
        for _ in range(10):
            container.scroll_down()
        
        # 強制的に再描画
        self.refresh()
        
        after_y = container.scroll_y
        self.logger.debug(f"AFTER page_down: container.scroll_y={after_y}, delta={after_y - before_y}")
    
    def action_page_up(self) -> None:
        """Scroll up one page."""
        self.logger.debug("action_page_up called")
        container = self.query_one("#log-content-container")
        before_y = container.scroll_y
        self.logger.debug(f"BEFORE page_up: container.scroll_y={before_y}")
        
        # 10行分スクロール
        for _ in range(10):
            container.scroll_up()
        
        # 強制的に再描画
        self.refresh()
        
        after_y = container.scroll_y
        self.logger.debug(f"AFTER page_up: container.scroll_y={after_y}, delta={after_y - before_y}")
    
    def action_scroll_home(self) -> None:
        """Scroll to the top."""
        self.logger.debug("action_scroll_home called")
        container = self.query_one("#log-content-container")
        before_y = container.scroll_y
        self.logger.debug(f"BEFORE scroll_home: container.scroll_y={before_y}")
        
        # 先頭にスクロール
        container.scroll_home()
        
        # 強制的に再描画
        self.refresh()
        
        after_y = container.scroll_y
        self.logger.debug(f"AFTER scroll_home: container.scroll_y={after_y}, delta={after_y - before_y}")
    
    def action_scroll_end(self) -> None:
        """Scroll to the bottom."""
        self.logger.debug("action_scroll_end called")
        container = self.query_one("#log-content-container")
        before_y = container.scroll_y
        self.logger.debug(f"BEFORE scroll_end: container.scroll_y={before_y}")
        
        # 末尾にスクロール
        container.scroll_end()
        
        # 強制的に再描画
        self.refresh()
        
        after_y = container.scroll_y
        self.logger.debug(f"AFTER scroll_end: container.scroll_y={after_y}, delta={after_y - before_y}")
    
    def action_dismiss(self) -> None:
        """Dismiss the screen."""
        self.logger.debug("action_dismiss called")
        self.app.pop_screen()
    
    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        self.logger.debug("on_mount called")
        
        # ウィジェットの詳細情報を記録
        container = self.query_one("#log-content-container")
        
        self.logger.debug(f"Container: id={container.id}, class={container.__class__.__name__}")
        self.logger.debug(f"Container attributes: {dir(container)}")
        self.logger.debug(f"Container virtual_size={container.virtual_size}, size={container.size}")
        self.logger.debug(f"Container scroll_x={container.scroll_x}, scroll_y={container.scroll_y}")
        
        # 画面自体にフォーカスを当てる
        self.focus()
        self.logger.debug(f"LogViewerScreen focused: {self.has_focus}")
        
        # コンテナにフォーカスを当てる
        self.set_focus(container)
        self.logger.debug(f"Container focused: {container.has_focus}")
    
    def on_show(self) -> None:
        """Event handler called when the screen is shown."""
        self.logger.debug("on_show called")
        # 画面自体にフォーカスを当てる
        self.focus()
        self.logger.debug(f"LogViewerScreen shown and focused: {self.has_focus}")
        
        # コンテナにフォーカスを当てる
        container = self.query_one("#log-content-container")
        self.set_focus(container)
        self.logger.debug(f"Container focused on show: {container.has_focus}")
    
    def on_enter(self) -> None:
        """Event handler called when the screen is entered."""
        self.logger.debug("on_enter called")
        # 画面自体にフォーカスを当てる
        self.focus()
        self.logger.debug(f"LogViewerScreen entered and focused: {self.has_focus}")
        
        # コンテナにフォーカスを当てる
        container = self.query_one("#log-content-container")
        self.set_focus(container)
        self.logger.debug(f"Container focused on enter: {container.has_focus}")
    
    def on_focus(self) -> None:
        """Event handler called when the screen gains focus."""
        self.logger.debug("on_focus called")
        # コンテナにフォーカスを当てる
        container = self.query_one("#log-content-container")
        self.set_focus(container)
        self.logger.debug(f"Container focused on focus: {container.has_focus}")
    
    def on_key(self, event) -> None:
        """キーイベントを処理する"""
        self.logger.debug(f"on_key: {event.key}, focused: {self.has_focus}")
        
        # キーイベントをシンプルに処理し、バインディングに任せる
        # これにより、j/kキーなどのスクロール操作がBINDINGSを通じて処理される
        return False
    
    def on_idle(self) -> None:
        """アイドル時に呼び出され、フォーカス状態を監視"""
        container = self.query_one("#log-content-container")
        if not container.has_focus:
            self.logger.debug("Container lost focus, restoring...")
            self.set_focus(container)
