"""
ANSI escape sequence filtering and terminal output sanitization
"""

import re


class AnsiFilter:
    """Filter ANSI escape sequences and terminal control characters"""

    # ANSI escape sequence patterns
    ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[mK]")
    CURSOR_PATTERN = re.compile(r"\x1b\[[0-9;]*[ABCDEFHIJ]")
    CURSOR_POSITION_PATTERN = re.compile(r"\x1b\[[0-9;]*[Hf]")
    CURSOR_QUERY_PATTERN = re.compile(r"\x1b\[[0-9;]*R")
    SCREEN_CLEAR_PATTERN = re.compile(r"\x1b\[[0-9;]*[2J3J]")
    LINE_CLEAR_PATTERN = re.compile(r"\x1b\[[0-9;]*K")

    # Control characters
    CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")

    # Bell character
    BELL_CHAR = re.compile(r"\x07")

    # Backspace sequences
    BACKSPACE_PATTERN = re.compile(r"\x08+")

    @classmethod
    def strip_ansi_codes(cls, text: str) -> str:
        """Remove ANSI color codes and formatting sequences"""
        if not text:
            return text

        # Remove ANSI color and formatting codes
        text = cls.ANSI_ESCAPE_PATTERN.sub("", text)
        return text

    @classmethod
    def strip_cursor_controls(cls, text: str) -> str:
        """Remove cursor movement and positioning controls"""
        if not text:
            return text

        # Remove cursor controls
        text = cls.CURSOR_PATTERN.sub("", text)
        text = cls.CURSOR_POSITION_PATTERN.sub("", text)
        text = cls.CURSOR_QUERY_PATTERN.sub("", text)
        return text

    @classmethod
    def strip_screen_controls(cls, text: str) -> str:
        """Remove screen clearing and line clearing controls"""
        if not text:
            return text

        # Remove screen/line clearing
        text = cls.SCREEN_CLEAR_PATTERN.sub("", text)
        text = cls.LINE_CLEAR_PATTERN.sub("", text)
        return text

    @classmethod
    def strip_control_chars(cls, text: str) -> str:
        """Remove control characters except newline and tab"""
        if not text:
            return text

        # Remove control characters (but keep \n and \t)
        text = cls.CONTROL_CHARS.sub("", text)
        text = cls.BELL_CHAR.sub("", text)
        text = cls.BACKSPACE_PATTERN.sub("", text)
        return text

    @classmethod
    def sanitize_terminal_output(cls, text: str) -> str:
        """Comprehensive sanitization of terminal output"""
        if not text:
            return text

        # Apply all filters
        text = cls.strip_ansi_codes(text)
        text = cls.strip_cursor_controls(text)
        text = cls.strip_screen_controls(text)
        text = cls.strip_control_chars(text)

        # Clean up excessive whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)  # Multiple empty lines
        text = re.sub(r"[ \t]+\n", "\n", text)  # Trailing whitespace

        return text

    @classmethod
    def sanitize_msfconsole_output(cls, text: str) -> str:
        """Specialized sanitization for msfconsole output"""
        if not text:
            return text

        # First apply general sanitization
        text = cls.sanitize_terminal_output(text)

        # Remove msfconsole-specific patterns
        # Remove progress indicators and status messages
        text = re.sub(r"^\[\*\]\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\[!\]\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\[+\]\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\[-\]\s*", "", text, flags=re.MULTILINE)

        # Remove MSF prompt indicators
        text = re.sub(r"^msf\d*\s*>\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^msf\d*\s*exploit\([^)]+\)\s*>\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^msf\d*\s*auxiliary\([^)]+\)\s*>\s*", "", text, flags=re.MULTILINE)

        # Remove job status lines
        text = re.sub(r"^\[\*\]\s*Started\s+.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\[\*\]\s*Stopping\s+.*$", "", text, flags=re.MULTILINE)

        # Clean up remaining empty lines
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        text = text.strip()

        return text
