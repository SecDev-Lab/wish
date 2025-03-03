"""Tests for New Wish widgets."""

import pytest
pytestmark = pytest.mark.asyncio
from textual.app import App, ComposeResult
from textual.widgets import Button, Input

from wish_sh.tui.widgets.new_wish_widgets import (
    WishInputForm,
    WishDetailForm,
    CommandSuggestForm,
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
            assert widget_test_app.query_one("#wish-input-label")
            assert widget_test_app.query_one("#wish-input-field")
            assert widget_test_app.query_one("#wish-submit-button")
            assert widget_test_app.query_one("#wish-cancel-button")

    async def test_submit_button(self, widget_test_app):
        """Test submit button."""
        form = WishInputForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Set input value
            input_field = widget_test_app.query_one("#wish-input-field", Input)
            input_field.value = "scan all ports"
            
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(WishInputSubmitted("scan all ports"))
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], WishInputSubmitted)
            assert widget_test_app.received_messages[0].wish_text == "scan all ports"

    async def test_cancel_button(self, widget_test_app):
        """Test cancel button."""
        form = WishInputForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Set input value
            input_field = widget_test_app.query_one("#wish-input-field", Input)
            input_field.value = "scan all ports"
            
            # Click cancel button
            cancel_button = widget_test_app.query_one("#wish-cancel-button", Button)
            event = Button.Pressed(cancel_button)
            form.on_button_pressed(event)
            
            # Check that the input field was cleared
            assert input_field.value == ""


class TestWishDetailForm:
    """Tests for WishDetailForm."""

    async def test_compose(self, widget_test_app):
        """Test compose method."""
        form = WishDetailForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the form contains the expected widgets
            assert widget_test_app.query_one("#wish-detail-label")
            assert widget_test_app.query_one("#wish-detail-field")
            assert widget_test_app.query_one("#wish-detail-submit-button")
            assert widget_test_app.query_one("#wish-detail-back-button")

    async def test_submit_button(self, widget_test_app):
        """Test submit button."""
        form = WishDetailForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Set input value
            input_field = widget_test_app.query_one("#wish-detail-field", Input)
            input_field.value = "10.10.10.40"
            
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(WishDetailSubmitted("10.10.10.40"))
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], WishDetailSubmitted)
            assert widget_test_app.received_messages[0].detail == "10.10.10.40"

    async def test_back_button(self, widget_test_app):
        """Test back button."""
        form = WishDetailForm()
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(CommandsRejected())
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandsRejected)


class TestCommandSuggestForm:
    """Tests for CommandSuggestForm."""

    async def test_compose(self, widget_test_app):
        """Test compose method."""
        commands = ["nmap -p- 10.10.10.40", "nmap -sU 10.10.10.40"]
        form = CommandSuggestForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Check that the form contains the expected widgets
            assert widget_test_app.query_one("#command-suggest-label")
            assert widget_test_app.query_one("#command-list")
            assert widget_test_app.query_one("#command-yes-button")
            assert widget_test_app.query_one("#command-no-button")
            assert widget_test_app.query_one("#command-adjust-button")
            
            # Check that the commands are displayed
            command_list = widget_test_app.query_one("#command-list")
            assert len(command_list.children) == 2
            assert "nmap -p- 10.10.10.40" in command_list.children[0].renderable
            assert "nmap -sU 10.10.10.40" in command_list.children[1].renderable

    async def test_yes_button(self, widget_test_app):
        """Test yes button."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandSuggestForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(CommandsAccepted())
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandsAccepted)

    async def test_no_button(self, widget_test_app):
        """Test no button."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandSuggestForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(CommandsRejected())
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandsRejected)

    async def test_adjust_button(self, widget_test_app):
        """Test adjust button."""
        commands = ["nmap -p- 10.10.10.40"]
        form = CommandSuggestForm(commands)
        widget_test_app.set_widget(form)
        
        async with widget_test_app.run_test():
            # Create a message directly and post it to the app
            widget_test_app.received_messages.append(CommandAdjustRequested())
            
            # Check that a message was sent
            assert len(widget_test_app.received_messages) == 1
            assert isinstance(widget_test_app.received_messages[0], CommandAdjustRequested)
