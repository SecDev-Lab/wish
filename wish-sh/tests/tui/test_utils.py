"""Tests for the TUI utility functions."""

import pytest
from wish_sh.tui.utils import make_markup_safe, sanitize_command_text


class TestUtils:
    """Tests for the TUI utility functions."""

    def test_make_markup_safe_escapes_markup(self):
        """Test that make_markup_safe correctly escapes markup characters."""
        text = "This has [bold]markup[/bold] in it"
        result = make_markup_safe(text)
        # Rich's escape function escapes the brackets with a backslash
        assert "\\[bold]" in result
        assert "\\[/bold]" in result
        # The text should still be recognizable
        assert "This has" in result
        assert "markup" in result
        assert "in it" in result

    def test_make_markup_safe_handles_none(self):
        """Test that make_markup_safe returns an empty string when input is None."""
        result = make_markup_safe(None)
        assert result == ""

    def test_make_markup_safe_with_special_characters(self):
        """Test that make_markup_safe handles text with special characters."""
        text = "Text with [red]color[/red] and [b]bold[/b] and [i]italic[/i]"
        result = make_markup_safe(text)
        # All markup should be escaped
        assert "\\[red]" in result
        assert "\\[/red]" in result
        assert "\\[b]" in result
        assert "\\[/b]" in result
        assert "\\[i]" in result
        assert "\\[/i]" in result

    def test_sanitize_command_text_replaces_characters(self):
        """Test that sanitize_command_text correctly replaces problematic characters."""
        command = 'echo "Hello [world]" with \\ backslash'
        result = sanitize_command_text(command)
        assert '[' not in result
        assert ']' not in result
        assert '"' not in result
        assert '\\' not in result
        assert '【' in result
        assert '】' in result
        assert "'" in result
        assert '/' in result

    def test_sanitize_command_text_handles_none(self):
        """Test that sanitize_command_text returns an empty string when input is None."""
        result = sanitize_command_text(None)
        assert result == ""

    def test_sanitize_command_text_complex_command(self):
        """Test that sanitize_command_text handles complex commands."""
        complex_command = r'grep -r "pattern \[with brackets\]" --include="*.py" .'
        result = sanitize_command_text(complex_command)
        # All problematic characters should be replaced
        assert '"' not in result
        assert '[' not in result
        assert ']' not in result
        assert '\\' not in result
        # The command should still be recognizable
        assert 'grep -r' in result
        assert 'pattern' in result
        assert '--include=' in result
        assert '*.py' in result

    def test_sanitize_command_text_empty_string(self):
        """Test that sanitize_command_text handles empty strings."""
        result = sanitize_command_text("")
        assert result == ""

    def test_sanitize_command_text_no_special_chars(self):
        """Test that sanitize_command_text preserves text without special characters."""
        command = "simple command without special chars"
        result = sanitize_command_text(command)
        assert result == command
