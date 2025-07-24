"""Minimal input-only Textual app for wish."""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, OptionList, RichLog, TextArea
from textual.widgets.option_list import Option

# Completion-related imports removed - no longer needed

logger = logging.getLogger(__name__)


class ApprovalModal(ModalScreen[str]):
    """Approval modal dialog"""

    CSS = """
    ApprovalModal {
        align: center middle;
    }

    #approval-dialog {
        width: 60;
        height: 15;
        background: $surface;
        border: thick $accent;
        border-title-color: $accent;
        border-title-style: bold;
    }

    #approval-content {
        padding: 1;
        height: 100%;
    }

    #approval-options {
        height: 8;
        border: round $primary;
        margin-top: 1;
    }

    OptionList {
        background: $surface;
        color: $text;
    }

    OptionList:focus {
        border: round $accent;
    }

    OptionList > .option-list--option {
        padding: 0 1;
    }

    OptionList > .option-list--option-highlighted {
        background: $primary;
        color: $text;
    }

    OptionList > .option-list--option-selected {
        background: $accent;
        color: $text;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "select", "Select"),
        ("up", "cursor_up", "Up"),
        ("down", "cursor_down", "Down"),
        ("ctrl+p", "cursor_up", "Up"),
        ("ctrl+n", "cursor_down", "Down"),
        ("y", "select_yes", "Yes"),
        ("e", "select_edit", "Edit"),
        ("r", "select_revise", "Revise"),
        ("c", "select_copy", "Copy"),
    ]

    def __init__(self, plan: Any) -> None:
        super().__init__()
        self.plan = plan
        self.options = [
            Option("✅ Yes (Let's go!)", id="yes"),
            Option("📝 Edit", id="edit"),
            Option("🔁 Revise", id="revise"),
            Option("📋 Copy", id="copy"),
            Option("❌ Cancel", id="cancel"),
        ]

    def compose(self) -> ComposeResult:
        """Modal layout"""
        yield Container(
            Vertical(
                Label("◆ Run this script?", id="approval-title"),
                Label("Use arrow keys to navigate, Enter to select, Escape to cancel"),
                OptionList(*self.options, id="approval-options"),
                id="approval-content",
            ),
            id="approval-dialog",
        )

    def on_mount(self) -> None:
        """Processing when modal is displayed"""
        try:
            # Focus on option list
            option_list = self.query_one("#approval-options", OptionList)
            option_list.focus()
            # Select first option (Yes) by default
            option_list.highlighted = 0
            logger.info("ApprovalModal mounted successfully")
        except Exception as e:
            logger.error(f"Failed to mount ApprovalModal: {e}")
            # Fallback to cancel
            self.dismiss("cancel")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Processing when option is selected"""
        logger.info(f"Approval option selected: {event.option.id}")
        self.dismiss(event.option.id)

    def action_select(self) -> None:
        """Selection with Enter key"""
        option_list = self.query_one("#approval-options", OptionList)
        if option_list.highlighted is not None:
            selected_option = self.options[option_list.highlighted]
            logger.info(f"Approval selected via Enter: {selected_option.id}")
            self.dismiss(selected_option.id)

    def action_cancel(self) -> None:
        """Cancel with Escape key"""
        logger.info("Approval cancelled via Escape")
        self.dismiss("cancel")

    def action_cursor_up(self) -> None:
        """Up arrow key"""
        self.query_one("#approval-options", OptionList).action_cursor_up()

    def action_cursor_down(self) -> None:
        """Down arrow key"""
        self.query_one("#approval-options", OptionList).action_cursor_down()

    def action_select_yes(self) -> None:
        """Direct Yes selection with Y key"""
        logger.info("Direct yes selection via 'y' key")
        self.dismiss("yes")

    def action_select_edit(self) -> None:
        """Direct Edit selection with E key"""
        logger.info("Direct edit selection via 'e' key")
        self.dismiss("edit")

    def action_select_revise(self) -> None:
        """Direct Revise selection with R key"""
        logger.info("Direct revise selection via 'r' key")
        self.dismiss("revise")

    def action_select_copy(self) -> None:
        """Direct Copy selection with C key"""
        logger.info("Direct copy selection via 'c' key")
        self.dismiss("copy")


class PlanEditModal(ModalScreen[bool]):
    """Plan editing modal dialog"""

    CSS = """
    PlanEditModal {
        align: center middle;
    }

    #edit-dialog {
        width: 80;
        height: 20;
        background: $surface;
        border: thick $accent;
        border-title-color: $accent;
        border-title-style: bold;
    }

    #edit-content {
        padding: 1;
        height: 100%;
    }

    #edit-form {
        height: 1fr;
        margin-bottom: 1;
    }

    #edit-buttons {
        height: auto;
        align: center middle;
    }

    Input {
        margin: 0 0 1 0;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, plan: Any) -> None:
        super().__init__()
        self.plan = plan
        self.current_step = 0
        self.edited_plan = self._copy_plan(plan)

    def _copy_plan(self, original_plan: Any) -> Any:
        """Create deep copy of plan"""
        # Simple copy (adjust according to actual Plan object structure)
        import copy

        return copy.deepcopy(original_plan)

    def compose(self) -> ComposeResult:
        """Edit modal layout"""
        step = self.edited_plan.steps[self.current_step] if self.edited_plan.steps else None

        yield Container(
            Vertical(
                Label(f"📝 Edit Plan Step {self.current_step + 1}/{len(self.edited_plan.steps)}", id="edit-title"),
                Label("Use Tab to navigate between fields, Ctrl+S to save, Escape to cancel"),
                Container(
                    Input(
                        value=step.command if step else "",
                        placeholder="Enter command",
                        id="command-input",
                    ),
                    Input(
                        value=step.purpose if step else "",
                        placeholder="Purpose of this command",
                        id="purpose-input",
                    ),
                    Input(
                        value=step.expected_result if step else "",
                        placeholder="Expected result",
                        id="expected-input",
                    ),
                    id="edit-form",
                ),
                Container(
                    Button("⬅️ Previous", id="prev", disabled=self.current_step == 0),
                    Button("💾 Save & Next", id="next", variant="primary"),
                    Button("✅ Save & Execute", id="execute", variant="success"),
                    Button("❌ Cancel", id="cancel", variant="error"),
                    id="edit-buttons",
                ),
                id="edit-content",
            ),
            id="edit-dialog",
        )

    def on_mount(self) -> None:
        """Processing when edit modal is displayed"""
        try:
            # Focus on command input field
            command_input = self.query_one("#command-input", Input)
            command_input.focus()
            logger.info("PlanEditModal mounted successfully")
        except Exception as e:
            logger.error(f"Failed to mount PlanEditModal: {e}")
            self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Button press processing"""
        if event.button.id == "cancel":
            logger.info("Plan edit cancelled")
            self.dismiss(False)
        elif event.button.id == "prev":
            if self.current_step > 0:
                self._save_current_step()
                self.current_step -= 1
                self._refresh_display()
        elif event.button.id == "next":
            self._save_current_step()
            if self.current_step < len(self.edited_plan.steps) - 1:
                self.current_step += 1
                self._refresh_display()
            else:
                # For the last step, save and exit
                logger.info("Plan edit completed - all steps saved")
                self.dismiss(True)
        elif event.button.id == "execute":
            self._save_current_step()
            logger.info("Plan edit completed - executing edited plan")
            self.dismiss(True)

    def action_save(self) -> None:
        """Save with Ctrl+S"""
        self._save_current_step()
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel with Escape"""
        logger.info("Plan edit cancelled via Escape")
        self.dismiss(False)

    def _save_current_step(self) -> None:
        """Save editing content of current step"""
        if self.current_step < len(self.edited_plan.steps):
            step = self.edited_plan.steps[self.current_step]
            try:
                command_input = self.query_one("#command-input", Input)
                purpose_input = self.query_one("#purpose-input", Input)
                expected_input = self.query_one("#expected-input", Input)

                step.command = command_input.value.strip()
                step.purpose = purpose_input.value.strip()
                step.expected_result = expected_input.value.strip()

                logger.debug(f"Saved step {self.current_step}: {step.command}")
            except Exception as e:
                logger.error(f"Failed to save step {self.current_step}: {e}")

    def _refresh_display(self) -> None:
        """Update display content"""
        if self.current_step < len(self.edited_plan.steps):
            step = self.edited_plan.steps[self.current_step]
            try:
                # Update title
                title_label = self.query_one("#edit-title", Label)
                title_label.update(f"📝 Edit Plan Step {self.current_step + 1}/{len(self.edited_plan.steps)}")

                # Update input fields
                command_input = self.query_one("#command-input", Input)
                purpose_input = self.query_one("#purpose-input", Input)
                expected_input = self.query_one("#expected-input", Input)

                command_input.value = step.command
                purpose_input.value = step.purpose
                expected_input.value = step.expected_result

                # Update button state
                prev_button = self.query_one("#prev", Button)
                prev_button.disabled = self.current_step == 0

                logger.debug(f"Refreshed display for step {self.current_step}")
            except Exception as e:
                logger.error(f"Failed to refresh display: {e}")


class PlanReviseModal(ModalScreen[str]):
    """Plan revision request modal dialog"""

    CSS = """
    PlanReviseModal {
        align: center middle;
    }

    #revise-dialog {
        width: 70;
        height: 15;
        background: $surface;
        border: thick $accent;
        border-title-color: $accent;
        border-title-style: bold;
    }

    #revise-content {
        padding: 1;
        height: 100%;
    }

    #revise-form {
        height: 1fr;
        margin-bottom: 1;
    }

    #revise-buttons {
        height: auto;
        align: center middle;
    }

    TextArea {
        margin: 0 0 1 0;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self, plan: Any) -> None:
        super().__init__()
        self.plan = plan
        self.revision_request = ""

    def compose(self) -> ComposeResult:
        """Revision request modal layout"""
        yield Container(
            Vertical(
                Label("🔁 Revise Plan", id="revise-title"),
                Label("Describe what you'd like to improve (optional):"),
                Label("[dim]e.g., Make it more thorough, Use stealth options, Add more enumeration steps...[/dim]"),
                Container(
                    TextArea(
                        id="revision-input",
                    ),
                    id="revise-form",
                ),
                Container(
                    Button("🔄 Generate New Plan", id="submit", variant="primary"),
                    Button("❌ Cancel", id="cancel", variant="error"),
                    id="revise-buttons",
                ),
                id="revise-content",
            ),
            id="revise-dialog",
        )

    def on_mount(self) -> None:
        """Processing when revision request modal is displayed"""
        try:
            # Focus on text area
            revision_input = self.query_one("#revision-input", TextArea)
            revision_input.focus()
            logger.info("PlanReviseModal mounted successfully")
        except Exception as e:
            logger.error(f"Failed to mount PlanReviseModal: {e}")
            self.dismiss("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Button press processing"""
        if event.button.id == "cancel":
            logger.info("Plan revision cancelled")
            self.dismiss("")
        elif event.button.id == "submit":
            self._submit_revision_request()

    def action_submit(self) -> None:
        """Submit with Ctrl+S"""
        self._submit_revision_request()

    def action_cancel(self) -> None:
        """Cancel with Escape"""
        logger.info("Plan revision cancelled via Escape")
        self.dismiss("")

    def _submit_revision_request(self) -> None:
        """Submit revision request"""
        try:
            revision_input = self.query_one("#revision-input", TextArea)
            self.revision_request = revision_input.text.strip()
            logger.info(f"Submitting revision request: {self.revision_request[:100]}...")
            self.dismiss(self.revision_request)
        except Exception as e:
            logger.error(f"Failed to submit revision request: {e}")
            self.dismiss("")


class MinimalInputApp(App):
    """Minimal input-only Textual app - bottom fixed input field only"""

    # Settings for tmux compatibility
    _use_alternate_screen = False
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+c", "handle_ctrl_c", "Clear/Quit", priority=True),
        Binding("ctrl+s", "submit_command", "Submit command", priority=True),
        Binding("f1", "submit_command", "Submit command", priority=True),
        Binding("alt+enter", "submit_command", "Submit command", priority=True),
        Binding("ctrl+r", "toggle_thinking", "Toggle thinking mode", priority=True),
        Binding("ctrl+p", "handle_ctrl_p", "History back/Up", priority=True),
        Binding("ctrl+n", "handle_ctrl_n", "History forward/Down", priority=True),
        Binding("pageup", "scroll_up", "Scroll up", priority=True),
        Binding("pagedown", "scroll_down", "Scroll down", priority=True),
    ]

    CSS = """
    Screen {
        background: transparent;
    }

    #output-area {
        height: 1fr;
        margin: 0;
        border: none;
        background: transparent;
        scrollbar-size: 0 0;
        scrollbar-background: $panel;
        scrollbar-corner-color: $panel;
        padding-bottom: 3;
    }

    #input-container {
        height: auto;
        dock: bottom;
        background: #1e1e1e;
        border: round blue;
        padding: 0 1;
        margin: 0;
        /* Reliably prevent overlap with z-index */
        layer: above;
    }

    #main-input {
        border: none;
        background: transparent;
        padding: 0;
        margin: 0;
        height: auto;
        min-height: 1;
        max-height: 10;
        overflow: hidden;
    }

    #main-input:focus {
        border: none;
        background: transparent;
    }
    """

    def __init__(
        self,
        command_callback: Callable[[str], None] | None = None,
        state_manager: Any = None,
        job_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.dark = True

        # Disable fullscreen mode (strong setting)
        self.use_alternative_screen = False

        # Additional non-fullscreen settings
        try:
            self._screen_stack = []  # type: ignore[misc]  # Disable screen management
        except Exception:
            logger.debug("Failed to disable screen stack")

        # Command processing callback
        self.command_callback = command_callback

        # For detecting consecutive Ctrl+C presses
        self.last_ctrl_c_time = 0.0
        self.ctrl_c_timeout = 1.0

        # History management
        self.command_history: list[str] = []
        self.history_index = -1

        # thinking mode
        self.thinking_mode = False

        # Processing flag
        self.processing = False

        # Approval UI management
        self.approval_mode = False
        self.approval_result: str | None = None
        self.approval_callback: Callable[[str], None] | None = None
        self._pending_approval_setup: tuple[bool, Callable[[str], None] | None, Any] | None = None  # For delayed setup

        # Completion functionality removed - no longer needed

        # Output buffering (flicker prevention)
        self._output_buffer: list[str] = []
        self._flush_scheduled = False
        self._output_lock = asyncio.Lock()  # Synchronize output writing

        # Height adjustment debouncing
        self._height_adjust_scheduled = False
        self._last_height = 0  # Record previous height

    def compose(self) -> ComposeResult:
        """Integrated layout - output area + input field"""
        yield Vertical(
            # Output area
            RichLog(id="output-area", markup=True, wrap=True, auto_scroll=False),
            # Input field
            Container(
                TextArea(id="main-input"),
                id="input-container",
            ),
        )

    def on_mount(self) -> None:
        """Processing when app starts"""
        # Focus on input field
        text_area = self.query_one("#main-input", TextArea)

        # Set placeholder (execute in on_mount)
        try:
            text_area.placeholder = "Type your command here..."  # type: ignore[attr-defined]
        except Exception:
            # Ignore if placeholder is not supported
            logger.debug("TextArea does not support placeholder attribute")

        text_area.focus()

        # Execute initial height adjustment
        self._adjust_textarea_height(text_area)

        # Completion dropdown removed - no longer needed

        # Execute if there are delayed settings
        if self._pending_approval_setup:
            enabled, callback, plan = self._pending_approval_setup
            self._pending_approval_setup = None
            logger.info("Executing pending approval setup")
            self.set_approval_mode(enabled, callback, plan)

    def action_submit_command(self) -> None:
        """Submit command"""
        if self.processing:
            return  # Ignore during processing

        text_area = self.query_one("#main-input", TextArea)
        command = text_area.text.strip()

        if command:
            # Skip normal input processing in approval mode
            if self.approval_mode:
                logger.info(f"In approval mode, ignoring input: '{command}'")
                text_area.clear()
                return

            # Add to history
            self.command_history.append(command)
            self.history_index = len(self.command_history)

            # Process command
            if self.command_callback:
                self.processing = True
                try:
                    self.command_callback(command)
                finally:
                    self.processing = False

            # Clear TextArea
            text_area.clear()
            text_area.focus()

    def action_handle_ctrl_c(self) -> None:
        """Ctrl+C processing"""
        current_time = time.time()
        text_area = self.query_one("#main-input", TextArea)

        # Exit if within specified time from previous Ctrl+C
        if (current_time - self.last_ctrl_c_time) <= self.ctrl_c_timeout:
            self.exit()
        else:
            # First time: clear input
            if text_area.text.strip():
                text_area.clear()

        self.last_ctrl_c_time = current_time

    def action_handle_ctrl_p(self) -> None:
        """Ctrl+P processing: history back"""
        text_area = self.query_one("#main-input", TextArea)

        # Get cursor position
        cursor_line = text_area.cursor_location[0]
        total_lines = len(text_area.text.split("\n"))

        # If cursor is on single line or first line of multiple lines: history back
        if total_lines == 1 or cursor_line == 0:
            self._history_back()
        else:
            # Otherwise move cursor up one line
            text_area.action_cursor_up()

    def action_handle_ctrl_n(self) -> None:
        """Ctrl+N processing: history forward"""
        text_area = self.query_one("#main-input", TextArea)

        # Get cursor position
        cursor_line = text_area.cursor_location[0]
        total_lines = len(text_area.text.split("\n"))

        # If cursor is on single line or last line of multiple lines: history forward
        if total_lines == 1 or cursor_line == total_lines - 1:
            self._history_forward()
        else:
            # Otherwise move cursor down one line
            text_area.action_cursor_down()

    def _history_back(self) -> None:
        """Go back in history"""
        if not self.command_history:
            return

        if self.history_index > 0:
            self.history_index -= 1
            text_area = self.query_one("#main-input", TextArea)
            text_area.text = self.command_history[self.history_index]

    def _history_forward(self) -> None:
        """Go forward in history"""
        if not self.command_history:
            return

        text_area = self.query_one("#main-input", TextArea)

        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            text_area.text = self.command_history[self.history_index]
        else:
            # Clear when going beyond last history item
            self.history_index = len(self.command_history)
            text_area.clear()

    def action_toggle_thinking(self) -> None:
        """Ctrl+R: toggle thinking mode"""
        self.thinking_mode = not self.thinking_mode

        text_area = self.query_one("#main-input", TextArea)
        try:
            if self.thinking_mode:
                text_area.placeholder = "thinking... (Ctrl+R to toggle back)"  # type: ignore[attr-defined]
                if hasattr(text_area, "border_title"):
                    text_area.border_title = "Thinking Mode"
            else:
                text_area.placeholder = "Type your command here..."  # type: ignore[attr-defined]
                if hasattr(text_area, "border_title"):
                    text_area.border_title = None
        except Exception:
            # Ignore if error occurs
            logger.debug("Failed to update text area attributes")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Height adjustment when TextArea content changes (with debouncing)"""
        if event.text_area.id == "main-input":
            # Debounce height adjustment (execute after 50ms)
            if not self._height_adjust_scheduled:
                self._height_adjust_scheduled = True
                self.set_timer(0.05, lambda: self._debounced_height_adjust(event.text_area))

            # Completion dropdown removed - no longer needed
            self.showing_completions = False

    def _debounced_height_adjust(self, text_area: TextArea) -> None:
        """Debounced height adjustment"""
        self._height_adjust_scheduled = False
        self._adjust_textarea_height(text_area)

    def _adjust_textarea_height(self, text_area: TextArea) -> None:
        """Adjust TextArea height based on content and coordinate output area layout and scroll position"""
        lines = text_area.text.count("\n") + 1
        # Adjust height with minimum 1 line, maximum 10 lines
        new_height = max(1, min(lines, 10))

        # Dynamically update height with CSS
        current_height = getattr(text_area, "_current_height", None)
        if current_height == new_height:
            return  # Skip if no change

        text_area._current_height = new_height  # type: ignore[attr-defined]
        text_area.styles.height = new_height

        # Calculate total height of input container (TextArea + border + padding)
        # border: 1 (top) + 1 (bottom) = 2
        # padding: 0 (top) + 0 (bottom) = 0 (horizontal padding only)
        input_container_total_height = new_height + 2

        # Adjust output area
        output_area = self.query_one("#output-area")

        # 1. Adjust bottom padding (prevent overlap)
        output_area.styles.padding_bottom = input_container_total_height

        # 2. Remove dynamic max height calculation (causes flicker)
        # Changed to recalculate only on app resize

    def on_key(self, event: Key) -> None:
        """Key event processing."""
        # Tab key processing when TextArea has focus
        if event.key == "tab":
            focused_widget = self.focused
            if focused_widget and focused_widget.id == "main-input":
                # Completion dropdown removed - Tab key handling disabled
                pass
                event.prevent_default()
                event.stop()

    def _show_completions(self) -> None:
        """Show completion candidates - Removed, no longer needed."""
        pass

    def _apply_completion(self, item: Any) -> None:
        """Apply completion - Removed, no longer needed."""
        pass

    def set_command_callback(self, callback: Callable[[str], None]) -> None:
        """Set command processing callback"""
        self.command_callback = callback

    def get_command_history(self) -> list[str]:
        """Get command history"""
        return self.command_history.copy()

    def add_to_history(self, command: str) -> None:
        """Add to history (from external)"""
        if command not in self.command_history:
            self.command_history.append(command)
            self.history_index = len(self.command_history)

    def write_output(self, content: str) -> None:
        """Display content in output area (with buffering)"""
        # Add to buffer
        self._output_buffer.append(content)

        # Schedule flush if not already scheduled
        if not self._flush_scheduled:
            self._flush_scheduled = True
            # Flush after 10ms (batch process multiple consecutive writes)
            self.set_timer(0.01, self._schedule_flush_output_buffer)

    def _schedule_flush_output_buffer(self) -> None:
        """Synchronous wrapper method - schedule asynchronous flush"""
        # Use run_worker to execute async method
        self.run_worker(self._flush_output_buffer(), exclusive=False)

    async def _flush_output_buffer(self) -> None:
        """Flush buffered output (async with lock)"""
        async with self._output_lock:
            if not self._output_buffer:
                self._flush_scheduled = False
                return

            try:
                output_area = self.query_one("#output-area", RichLog)

                # Get buffer contents and clear
                buffer_copy = self._output_buffer.copy()
                self._output_buffer.clear()

                # Record current scroll position
                current_scroll = output_area.scroll_y
                max_scroll = output_area.virtual_size.height - output_area.size.height
                was_at_bottom = current_scroll >= max_scroll - 5

                # Write each line individually (using write_line)
                for line in buffer_copy:
                    # Process each line by splitting on newlines
                    for sub_line in line.split("\n"):
                        output_area.write_line(sub_line)

                # Auto-scroll only if user was near bottom
                if was_at_bottom:
                    # Immediate scroll with animate=False (prevent flicker)
                    output_area.scroll_end(animate=False)

            except Exception as e:
                # Fallback: display to standard output
                logger.debug(f"Failed to write to output area: {e}")
                for content in buffer_copy:
                    print(content)
            finally:
                self._flush_scheduled = False

    def clear_output(self) -> None:
        """Clear output area"""
        try:
            # Clear buffer too
            self._output_buffer.clear()
            self._flush_scheduled = False

            output_area = self.query_one("#output-area", RichLog)
            output_area.clear()

            # Reset scroll position
            output_area.scroll_home(animate=False)
        except Exception:
            logger.debug("Failed to clear output area")

    # Approval UI related methods
    def set_approval_mode(self, enabled: bool, callback: Callable[[str], None] | None = None, plan: Any = None) -> None:
        """Set approval mode"""
        logger.info(f"Setting approval mode: enabled={enabled}")
        self.approval_mode = enabled
        self.approval_result = None
        self.approval_callback = callback

        # Check if app is running
        if not self.is_running:
            logger.warning("App is not running, saving setup for later")
            # Save for later execution
            self._pending_approval_setup = (enabled, callback, plan)  # type: ignore[assignment]
            return

        if enabled:
            # Show approval in modal dialog
            logger.info("Showing approval modal")
            # Schedule async processing
            self.call_later(self._show_approval_modal, plan)
        else:
            # Return to normal mode
            logger.info("Approval mode disabled")

    def _show_approval_modal(self, plan: Any) -> None:
        """Show approval modal and wait for result"""

        async def show_modal_worker() -> None:
            try:
                logger.info("Starting approval modal worker")

                # Create modal instance
                modal = ApprovalModal(plan)
                logger.debug(f"Created ApprovalModal instance: {modal}")

                # Show modal and wait for result
                logger.debug("Calling push_screen_wait...")
                result = await self.push_screen_wait(modal)
                logger.info(f"Approval modal completed successfully with result: {result}")

                # Validate result
                if result not in ["yes", "edit", "revise", "copy", "cancel"]:
                    logger.warning(f"Unexpected modal result: {result}, treating as cancel")
                    result = "cancel"

                # Execute callback
                if self.approval_callback:
                    logger.debug(f"Executing approval callback with result: {result}")
                    self.approval_callback(result)
                else:
                    logger.warning("No approval callback set, result will be lost")

                # Disable approval mode
                self.approval_mode = False
                self.approval_result = result  # type: ignore[assignment]

            except Exception as e:
                import traceback

                logger.error(f"Failed to show approval modal: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")

                # Check app state
                if not self.is_running:
                    logger.error("App is not running, cannot display modal")
                elif not hasattr(self, "_screen_stack"):
                    logger.error("App screen stack not initialized")

                # Treat as cancel on error
                logger.info("Executing error fallback: treating as cancel")
                if self.approval_callback:
                    self.approval_callback("cancel")
                else:
                    logger.error("No approval callback available for error handling")

                self.approval_mode = False
                self.approval_result = "cancel"  # type: ignore[assignment]

        # Execute in worker context using run_worker
        try:
            logger.debug("Scheduling modal worker with run_worker")
            self.run_worker(show_modal_worker(), exclusive=False)
            logger.debug("Modal worker scheduled successfully")
        except Exception as e:
            logger.error(f"Failed to schedule modal worker: {e}")
            # Immediate cancel processing
            if self.approval_callback:
                self.approval_callback("cancel")
            self.approval_mode = False

    # Legacy action methods removed (handled by modal dialog)

    def action_scroll_up(self) -> None:
        """Page Up: scroll output area up"""
        try:
            output_area = self.query_one("#output-area", RichLog)
            output_area.scroll_page_up()
        except Exception:
            logger.debug("Failed to scroll up")

    def action_scroll_down(self) -> None:
        """Page Down: scroll output area down"""
        try:
            output_area = self.query_one("#output-area", RichLog)
            output_area.scroll_page_down()
        except Exception:
            logger.debug("Failed to scroll down")

    # Complete override of screen control (force non-fullscreen)
    def _enter_alt_screen(self) -> None:
        """Disable alternate screen mode start"""
        pass  # Do nothing

    def _exit_alt_screen(self) -> None:
        """Disable alternate screen mode exit"""
        pass  # Do nothing

    async def run_async(self, **kwargs: Any) -> Any:
        """Force execution in non-fullscreen mode"""
        # Ensure inline=True is set
        kwargs["inline"] = True
        kwargs["mouse"] = True

        # Optimize terminal control
        import os

        # Completely disable animations (prevent flicker)
        os.environ["TEXTUAL_ANIMATIONS"] = "none"

        # Additional settings for tmux environment
        if "TMUX" in os.environ:
            kwargs["headless"] = False

        try:
            return await super().run_async(**kwargs)
        except Exception as e:
            # Error handling
            logger.error(f"Textual app error: {e}")
            print(f"Textual app error: {e}")
            return None
