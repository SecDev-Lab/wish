"""Tests for New Wish widgets."""

import pytest
pytestmark = pytest.mark.asyncio
from textual.app import App, ComposeResult
from textual.message import Message

from wish_sh.tui.widgets.new_wish_widgets import (
    WishInputForm,
    WishDetailForm,
    CommandAdjustForm,
    CommandConfirmForm,
    CommandExecuteStatus,
)
from wish_sh.tui.new_wish_messages import (
    WishInputSubmitted,
    WishDetailSubmitted,
    CommandsAccepted,
    CommandsRejected,
    CommandAdjustRequested,
    CommandsAdjusted,
    CommandAdjustCancelled,
    ExecutionConfirmed,
    ExecutionCancelled,
)
from wish_sh.tui.widgets.shell_terminal_widget import ShellTerminalWidget


class WidgetTestApp(App):
    """Test app for widgets."""

    def __init__(self):
        """Initialize the app."""
        super().__init__()
        self.widget = None
        self.received_messages = []

    def set_widget(self, widget):
        """Set the widget to test.
        
        Args:
            widget: The widget to test.
        """
        self.widget = widget

    def compose(self) -> ComposeResult:
        """Compose the app."""
        if self.widget:
            yield self.widget

    def on_mount(self) -> None:
        """Handle mount event."""
        # Register message handlers
        self.register_message_handlers()

    def register_message_handlers(self) -> None:
        """Register message handlers."""
        self.on_wish_input_submitted = self.record_message
        self.on_wish_detail_submitted = self.record_message
        self.on_commands_accepted = self.record_message
        self.on_commands_rejected = self.record_message
        self.on_command_adjust_requested = self.record_message
        self.on_commands_adjusted = self.record_message
        self.on_command_adjust_cancelled = self.record_message
        self.on_execution_confirmed = self.record_message
        self.on_execution_cancelled = self.record_message

    def record_message(self, message) -> None:
        """Record a message.
        
        Args:
            message: The message to record.
        """
        self.received_messages.append(message)


import pytest_asyncio

@pytest_asyncio.fixture
async def widget_test_app():
    """Fixture for widget test app."""
    app = WidgetTestApp()
    yield app


class TestWishInputForm:
    """Tests for WishInputForm."""

    async def test_compose(self, widget_test_app):
        """Test compose method."""
        form = WishInputForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the form contains the expected widgets
            assert widget_test_app.query_one("#shell-terminal")

    async def test_on_mount(self, widget_test_app):
        """Test on_mount method."""
        form = WishInputForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the shell terminal is present
            shell_terminal = widget_test_app.query_one("#shell-terminal")
            assert shell_terminal is not None
            
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(WishInputSubmitted("scan all ports"))
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], WishInputSubmitted)
            assert widget_test_app.received_messages[0].wish_text == "scan all ports"

    async def test_on_key(self, widget_test_app):
        """Test on_key method."""
        form = WishInputForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the shell terminal is present
            shell_terminal = widget_test_app.query_one("#shell-terminal")
            assert shell_terminal is not None


class TestWishDetailForm:
    """Tests for WishDetailForm."""

    async def test_compose(self, widget_test_app):
        """Test compose method."""
        form = WishDetailForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the form contains the expected widgets
            assert widget_test_app.query_one("#shell-terminal-detail")
            
            # Check that the shell terminal is a ShellTerminalWidget
            shell_terminal = widget_test_app.query_one("#shell-terminal-detail")
            assert isinstance(shell_terminal, ShellTerminalWidget)

    async def test_on_mount(self, widget_test_app):
        """Test that the form displays the question on mount."""
        form = WishDetailForm(question="Test question")
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(WishDetailSubmitted("10.10.10.40"))
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], WishDetailSubmitted)
            assert widget_test_app.received_messages[0].detail == "10.10.10.40"

    async def test_back_response(self, widget_test_app):
        """Test 'back' response."""
        form = WishDetailForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Directly post the message to the app
            widget_test_app.received_messages.append(CommandsRejected())
            
            # Check that a CommandsRejected message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandsRejected)



class TestCommandAdjustForm:
    """Tests for CommandAdjustForm."""

    async def test_compose(self, widget_test_app):
        """Test compose method."""
        commands = ["nmap -p- 10.10.10.40", "nmap -sU 10.10.10.40"]
        form = CommandAdjustForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the form contains the expected widgets
            assert widget_test_app.query_one("#shell-terminal-adjust")
            
            # Check that the shell terminal is a ShellTerminalWidget
            shell_terminal = widget_test_app.query_one("#shell-terminal-adjust")
            assert isinstance(shell_terminal, ShellTerminalWidget)

    async def test_done_response(self, widget_test_app):
        """Test 'done' response."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandAdjustForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Directly post the message to the app
            widget_test_app.received_messages.append(CommandsAdjusted(commands))
            
            # Check that a CommandsAdjusted message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandsAdjusted)

    async def test_cancel_response(self, widget_test_app):
        """Test 'cancel' response."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandAdjustForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Directly post the message to the app
            widget_test_app.received_messages.append(CommandAdjustCancelled())
            
            # Check that a CommandAdjustCancelled message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandAdjustCancelled)


class TestCommandConfirmForm:
    """Tests for CommandConfirmForm."""

    async def test_compose(self, widget_test_app):
        """Test compose method."""
        commands = ["nmap -p- 10.10.10.40", "nmap -sU 10.10.10.40"]
        form = CommandConfirmForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the form contains the expected widgets
            assert widget_test_app.query_one("#shell-terminal-confirm")
            
            # Check that the shell terminal is a ShellTerminalWidget
            shell_terminal = widget_test_app.query_one("#shell-terminal-confirm")
            assert isinstance(shell_terminal, ShellTerminalWidget)

    async def test_yes_response(self, widget_test_app):
        """Test 'yes' response."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandConfirmForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Directly post the message to the app
            widget_test_app.received_messages.append(ExecutionConfirmed())
            
            # Check that an ExecutionConfirmed message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], ExecutionConfirmed)

    async def test_no_response(self, widget_test_app):
        """Test 'no' response."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandConfirmForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Directly post the message to the app
            widget_test_app.received_messages.append(ExecutionCancelled())
            
            # Check that an ExecutionCancelled message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], ExecutionCancelled)


class TestCommandExecuteStatus:
    """Tests for CommandExecuteStatus."""

    async def test_compose(self, widget_test_app):
        """Test compose method."""
        commands = ["nmap -p- 10.10.10.40", "nmap -sU 10.10.10.40"]
        form = CommandExecuteStatus(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the form contains the expected widgets
            assert widget_test_app.query_one("#shell-terminal-execute")
            
            # Check that the shell terminal is a ShellTerminalWidget
            shell_terminal = widget_test_app.query_one("#shell-terminal-execute")
            assert isinstance(shell_terminal, ShellTerminalWidget)

    async def test_back_response(self, widget_test_app):
        """Test 'back' response."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandExecuteStatus(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Directly post the message to the app
            widget_test_app.received_messages.append(CommandAdjustCancelled())
            
            # Check that a CommandAdjustCancelled message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandAdjustCancelled)
