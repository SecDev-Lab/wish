#!/usr/bin/env python3
"""テスト用モーダルダイアログアプリケーション"""

import sys
import logging
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static, Button

# 長いテキストを生成（スクロールテスト用）
LONG_TEXT = "\n".join([f"Line {i+1}: This is a test line for scrolling functionality." for i in range(100)])

# デバッグ用のロガーを設定
logger = logging.getLogger("test_modal")
logger.setLevel(logging.DEBUG)

# ファイルハンドラーを設定
try:
    handler = logging.FileHandler("/tmp/test_modal.log")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # コンソールハンドラーも追加
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.debug("Logger initialized")
except Exception as e:
    print(f"Failed to initialize logger: {e}")

class TestModalScreen(Screen):
    """テスト用モーダルダイアログ画面"""
    
    BINDINGS = [
        Binding("j", "scroll_down", "Scroll Down"),
        Binding("k", "scroll_up", "Scroll Up"),
        Binding("f", "page_down", "Page Down"),
        Binding("b", "page_up", "Page Up"),
        Binding("g", "scroll_home", "Top"),
        Binding("G", "scroll_end", "Bottom"),
        Binding("o", "view_output", "View Output"),
        Binding("e", "view_error", "View Error"),
        Binding("escape", "dismiss", "Close"),
    ]
    
    def compose(self) -> ComposeResult:
        """画面の構成要素を定義"""
        yield Static("テストモーダルダイアログ", id="modal-title")
        with ScrollableContainer(id="modal-container"):
            yield Static(LONG_TEXT, id="modal-content", markup=False)
        yield Static("Press j/k to scroll, o/e for output/error, ESC to close", id="modal-footer")
    
    def on_mount(self) -> None:
        """画面がマウントされたときの処理"""
        logger.debug("TestModalScreen mounted")
        container = self.query_one("#modal-container")
        content = self.query_one("#modal-content")
        logger.debug(f"Container: virtual_size={container.virtual_size}, size={container.size}")
        logger.debug(f"Container scroll_position: x={container.scroll_x}, y={container.scroll_y}")
        logger.debug(f"Content size: {content.size}")
    
    def action_scroll_down(self) -> None:
        """下にスクロール"""
        logger.debug("action_scroll_down called")
        container = self.query_one("#modal-container")
        before_y = container.scroll_y
        container.scroll_down()
        after_y = container.scroll_y
        logger.debug(f"Scroll down: {before_y} -> {after_y}, delta={after_y - before_y}")
    
    def action_scroll_up(self) -> None:
        """上にスクロール"""
        logger.debug("action_scroll_up called")
        container = self.query_one("#modal-container")
        before_y = container.scroll_y
        container.scroll_up()
        after_y = container.scroll_y
        logger.debug(f"Scroll up: {before_y} -> {after_y}, delta={after_y - before_y}")
    
    def action_page_down(self) -> None:
        """1ページ下にスクロール"""
        logger.debug("action_page_down called")
        container = self.query_one("#modal-container")
        before_y = container.scroll_y
        # 10行分スクロール
        for _ in range(10):
            container.scroll_down()
        after_y = container.scroll_y
        logger.debug(f"Page down: {before_y} -> {after_y}, delta={after_y - before_y}")
    
    def action_page_up(self) -> None:
        """1ページ上にスクロール"""
        logger.debug("action_page_up called")
        container = self.query_one("#modal-container")
        before_y = container.scroll_y
        # 10行分スクロール
        for _ in range(10):
            container.scroll_up()
        after_y = container.scroll_y
        logger.debug(f"Page up: {before_y} -> {after_y}, delta={after_y - before_y}")
    
    def action_scroll_home(self) -> None:
        """先頭にスクロール"""
        logger.debug("action_scroll_home called")
        container = self.query_one("#modal-container")
        before_y = container.scroll_y
        container.scroll_home()
        after_y = container.scroll_y
        logger.debug(f"Scroll home: {before_y} -> {after_y}, delta={after_y - before_y}")
    
    def action_scroll_end(self) -> None:
        """末尾にスクロール"""
        logger.debug("action_scroll_end called")
        container = self.query_one("#modal-container")
        before_y = container.scroll_y
        container.scroll_end()
        after_y = container.scroll_y
        logger.debug(f"Scroll end: {before_y} -> {after_y}, delta={after_y - before_y}")
    
    def action_view_output(self) -> None:
        """出力を表示"""
        logger.debug("action_view_output called")
        self.notify("Output view requested (o key pressed)")
    
    def action_view_error(self) -> None:
        """エラーを表示"""
        logger.debug("action_view_error called")
        self.notify("Error view requested (e key pressed)")
    
    def action_dismiss(self) -> None:
        """画面を閉じる"""
        logger.debug("action_dismiss called")
        self.app.exit()
    
    def on_key(self, event) -> None:
        """キーイベントを処理"""
        logger.debug(f"Key pressed: {event.key}")
        # キーイベントをそのまま処理する（親クラスの呼び出しは不要）
        return False

class TestModalApp(App):
    """テスト用モーダルアプリケーション"""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #modal-title {
        background: $primary;
        color: $text-primary;
        text-align: center;
        width: 100%;
        height: 1;
    }
    
    #modal-container {
        width: 80%;
        height: 20;
        border: tall $accent;
        overflow-y: scroll;
    }
    
    #modal-content {
        width: 100%;
    }
    
    #modal-footer {
        dock: bottom;
        background: $surface-darken-1;
        height: 1;
        text-align: center;
    }
    """
    
    def compose(self) -> ComposeResult:
        """アプリケーションの構成要素を定義"""
        yield TestModalScreen()

def main():
    """アプリケーションのエントリポイント"""
    logger.debug("Starting TestModalApp")
    app = TestModalApp()
    app.run()

if __name__ == "__main__":
    main()
