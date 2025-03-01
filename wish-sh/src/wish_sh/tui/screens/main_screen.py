"""Main screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen

from wish_sh.tui.widgets.help_pane import HelpPane
from wish_sh.tui.widgets.main_pane import MainPane
from wish_sh.tui.widgets.sub_pane import SubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane


class MainScreen(Screen):
    """Main screen for the wish-sh TUI application."""

    DEFAULT_CSS = """
    MainScreen {
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1fr 1fr;
        grid-columns: 30 1fr;
        grid-gutter: 1;
    }
    
    WishSelectPane {
        row-span: 2;
        column-span: 1;
    }
    
    MainPane {
        row-span: 1;
        column-span: 1;
    }
    
    SubPane {
        row-span: 1;
        column-span: 1;
    }
    
    HelpPane {
        layer: overlay;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        # Create the main layout
        self.wish_select = WishSelectPane(id="wish-select")
        self.main_pane = MainPane(id="main-pane")
        self.sub_pane = SubPane(id="sub-pane")
        help_pane = HelpPane(id="help-pane")

        # Yield the widgets in the desired order
        yield self.wish_select
        yield self.main_pane
        yield self.sub_pane
        yield help_pane

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        # Set initial focus to the main pane
        self.main_pane.focus()
        
        # Set initial active state
        self.wish_select.set_active(False)
        self.main_pane.set_active(True)
        self.sub_pane.set_active(False)
    
    def on_key(self, event) -> None:
        """Handle key events."""
        if event.key == "ctrl+left":
            self.activate_pane("wish-select")
        elif event.key == "ctrl+up":
            self.activate_pane("main-pane")
        elif event.key == "ctrl+down":
            self.activate_pane("sub-pane")
    
    def activate_pane(self, pane_id: str) -> None:
        """Activate the specified pane."""
        # Deactivate all panes
        self.wish_select.set_active(False)
        self.main_pane.set_active(False)
        self.sub_pane.set_active(False)
        
        # Activate the specified pane
        if pane_id == "wish-select":
            self.wish_select.set_active(True)
            self.wish_select.focus()
        elif pane_id == "main-pane":
            self.main_pane.set_active(True)
            self.main_pane.focus()
        elif pane_id == "sub-pane":
            self.sub_pane.set_active(True)
            self.sub_pane.focus()
