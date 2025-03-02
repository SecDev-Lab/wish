"""Textual application for wish-sh TUI."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static

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
        Binding("right", "focus_main", "Focus Main"),
        Binding("ctrl+up", "focus_main", "Focus Main"),
        Binding("ctrl+down", "focus_sub", "Focus Sub"),
        Binding("j", "scroll_down_line", "Scroll Down"),
        Binding("down", "scroll_down_line", "Scroll Down"),
        Binding("k", "scroll_up_line", "Scroll Up"),
        Binding("up", "scroll_up_line", "Scroll Up"),
        Binding("ctrl+f", "scroll_page_down", "Page Down"),
        Binding("ctrl+b", "scroll_page_up", "Page Up"),
        Binding(">", "scroll_end", "Bottom"),
        Binding("<", "scroll_home", "Top"),
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
        # デバッグログを追加
        print("action_focus_sub called")
        
        # Get the main screen
        main_screen = self.screen
        if hasattr(main_screen, "activate_pane"):
            print(f"Calling main_screen.activate_pane('sub-pane')")
            main_screen.activate_pane("sub-pane")
        else:
            print(f"Calling self.query_one('#sub-pane').focus()")
            self.query_one("#sub-pane").focus()

    def action_confirm_quit(self) -> None:
        """Action to show quit confirmation dialog."""
        from wish_sh.tui.screens.quit_screen import QuitScreen
        self.push_screen(QuitScreen())
    
    def action_scroll_up_line(self) -> None:
        """Scroll up one line in the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            # 1行上にスクロール
            content.scroll_up()
    
    def action_scroll_down_line(self) -> None:
        """Scroll down one line in the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            # 1行下にスクロール
            content.scroll_down()
    
    def action_scroll_page_up(self) -> None:
        """Page up in the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            # ページ単位でスクロール
            content.scroll_page_up()
    
    def action_scroll_page_down(self) -> None:
        """Page down in the active pane."""
        active_pane = self.get_active_pane()
        if active_pane and active_pane.id == "sub-pane":
            content = active_pane.query_one("#sub-pane-content")
            # ページ単位でスクロール
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
        if hasattr(main_screen, "wish_select") and main_screen.wish_select.has_class("active-pane"):
            return main_screen.wish_select
        elif hasattr(main_screen, "main_pane") and main_screen.main_pane.has_class("active-pane"):
            return main_screen.main_pane
        elif hasattr(main_screen, "sub_pane") and main_screen.sub_pane.has_class("active-pane"):
            return main_screen.sub_pane
        return None
    
    def on_key(self, event) -> None:
        """アプリケーション全体でのキーイベント監視"""
        # すべてのキーイベントをログに記録
        print(f"App received key: {event.key}")
        
        # Ctrl+下矢印のデバッグログを追加
        if event.key in ("ctrl+down", "ctrl+arrow_down", "down+ctrl"):
            print(f"App: Ctrl+Down key detected: {event.key}")
        
        # LogViewerScreen が表示されている場合、キーイベントを優先的に処理
        from wish_sh.tui.screens.log_viewer_screen import LogViewerScreen
        if isinstance(self.screen, LogViewerScreen):
            # キーイベントをログに記録
            print(f"App received key: {event.key} for LogViewerScreen")
            # LogViewerScreen のキーイベント処理を呼び出す
            result = self.screen.on_key(event)
            print(f"LogViewerScreen on_key result: {result}")
            return result
        
        # 通常のキーイベント処理
        return False
