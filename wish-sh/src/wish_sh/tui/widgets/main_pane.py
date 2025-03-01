"""Main Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class MainPane(Container):
    """Main content pane."""

    DEFAULT_CSS = """
    MainPane {
        width: 100%;
        height: 100%;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    
    MainPane.active-pane {
        border: heavy $error;
        background: $warning-lighten-2;
    }
    
    #main-pane-active-title {
        color: $success;
        text-style: bold;
    }
    
    #main-pane-inactive-title {
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        self.active_title = Static("[Active] Main Pane", id="main-pane-active-title")
        self.inactive_title = Static("Main Pane", id="main-pane-inactive-title")
        
        # Initially, Main pane is active
        self.active_title.styles.display = "block"
        self.inactive_title.styles.display = "none"
        
        yield self.active_title
        yield self.inactive_title
        yield Static("(Main content will be displayed here)", id="main-pane-content")
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the pane."""
        if active:
            # タイトル表示の切り替え
            self.active_title.styles.display = "block"
            self.inactive_title.styles.display = "none"
            
            # ペーン自体のスタイル変更
            self.add_class("active-pane")
        else:
            # タイトル表示の切り替え
            self.active_title.styles.display = "none"
            self.inactive_title.styles.display = "block"
            
            # ペーン自体のスタイルを元に戻す
            self.remove_class("active-pane")
