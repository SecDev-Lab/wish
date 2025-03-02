"""Utility functions for the TUI."""

from rich.markup import escape
from wish_models.command_result.command_state import CommandState


def make_markup_safe(text: str) -> str:
    """Make text safe for display in Rich markup.
    
    This function escapes any characters that might be interpreted as markup
    by Rich, ensuring the text is displayed as-is.
    
    Args:
        text: The text to make safe.
        
    Returns:
        The safe text.
    """
    if text is None:
        return ""
    
    # Use Rich's built-in escape function to handle markup characters
    return escape(text)


def sanitize_command_text(command: str) -> str:
    """Sanitize command text for display in the TUI.
    
    This function replaces problematic characters in command text that might
    cause issues with display or interpretation.
    
    Args:
        command: The command text to sanitize.
        
    Returns:
        The sanitized command text.
    """
    if command is None:
        return ""
    
    # Replace problematic characters in command text
    safe_command = command
    # Replace characters that might be interpreted as markup or cause issues
    safe_command = safe_command.replace("[", "【").replace("]", "】")
    safe_command = safe_command.replace('"', "'")
    safe_command = safe_command.replace("\\", "/")
    return safe_command


def get_command_state_emoji(state):
    """Get emoji for command state.
    
    Args:
        state: The CommandState enum value.
        
    Returns:
        str: The emoji representing the state.
    """
    if state == CommandState.DOING:
        return "🔄"
    elif state == CommandState.SUCCESS:
        return "✅"
    elif state == CommandState.USER_CANCELLED:
        return "🚫"
    elif state == CommandState.COMMAND_NOT_FOUND:
        return "🔍❌"
    elif state == CommandState.FILE_NOT_FOUND:
        return "📄❌"
    elif state == CommandState.REMOTE_OPERATION_FAILED:
        return "🌐❌"
    elif state == CommandState.TIMEOUT:
        return "⏱️"
    elif state == CommandState.NETWORK_ERROR:
        return "📡❌"
    elif state == CommandState.OTHERS:
        return "❌"
    else:
        return "❓"
