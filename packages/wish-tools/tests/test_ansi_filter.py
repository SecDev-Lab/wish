"""
Tests for ANSI escape sequence filtering
"""

import pytest

from wish_tools.execution.ansi_filter import AnsiFilter


class TestAnsiFilter:
    """Test ANSI escape sequence filtering functionality"""

    def test_strip_ansi_codes(self):
        """Test ANSI color code removal"""
        # Test with color codes
        text_with_colors = "\x1b[31mRed text\x1b[0m\x1b[32mGreen text\x1b[0m"
        expected = "Red textGreen text"
        assert AnsiFilter.strip_ansi_codes(text_with_colors) == expected

        # Test with formatting codes
        text_with_format = "\x1b[1mBold\x1b[0m \x1b[4mUnderline\x1b[0m"
        expected = "Bold Underline"
        assert AnsiFilter.strip_ansi_codes(text_with_format) == expected

        # Test empty string
        assert AnsiFilter.strip_ansi_codes("") == ""

        # Test text without ANSI codes
        plain_text = "Plain text"
        assert AnsiFilter.strip_ansi_codes(plain_text) == plain_text

    def test_strip_cursor_controls(self):
        """Test cursor control sequence removal"""
        # Test cursor position queries (the problem characters)
        text_with_cursor = "Normal text\x1b[1;1R\x1b[1;1R\x1b[1;1RMore text"
        expected = "Normal textMore text"
        assert AnsiFilter.strip_cursor_controls(text_with_cursor) == expected

        # Test cursor movement
        text_with_movement = "Text\x1b[2A\x1b[3B\x1b[4C\x1b[5D"
        expected = "Text"
        assert AnsiFilter.strip_cursor_controls(text_with_movement) == expected

        # Test cursor positioning
        text_with_pos = "Text\x1b[10;20H\x1b[5;5f"
        expected = "Text"
        assert AnsiFilter.strip_cursor_controls(text_with_pos) == expected

    def test_strip_screen_controls(self):
        """Test screen clearing control removal"""
        # Test screen clearing
        text_with_clear = "Text\x1b[2J\x1b[3JMore text"
        expected = "TextMore text"
        assert AnsiFilter.strip_screen_controls(text_with_clear) == expected

        # Test line clearing
        text_with_line_clear = "Text\x1b[KMore text"
        expected = "TextMore text"
        assert AnsiFilter.strip_screen_controls(text_with_line_clear) == expected

    def test_strip_control_chars(self):
        """Test control character removal"""
        # Test with bell and backspace
        text_with_controls = "Text\x07\x08\x08Normal"
        expected = "TextNormal"
        assert AnsiFilter.strip_control_chars(text_with_controls) == expected

        # Test preserving newlines and tabs
        text_with_whitespace = "Line1\nLine2\tTabbed"
        assert AnsiFilter.strip_control_chars(text_with_whitespace) == text_with_whitespace

    def test_sanitize_terminal_output(self):
        """Test comprehensive terminal output sanitization"""
        # Complex example with multiple types of escape sequences
        complex_text = "\x1b[31mRed\x1b[0m\x1b[1;1R\x1b[1;1RNormal\x1b[2J\x07\x08Text\n\n\n\x1b[32mGreen\x1b[0m"

        result = AnsiFilter.sanitize_terminal_output(complex_text)

        # Should remove all ANSI codes, cursor controls, screen controls, and control chars
        # Should clean up excessive whitespace
        expected = "RedNormalText\n\nGreen"
        assert result == expected

    def test_sanitize_msfconsole_output(self):
        """Test msfconsole-specific output sanitization"""
        # Simulate msfconsole output with status indicators
        msfconsole_output = (
            "\x1b[31m[*] Starting handler\x1b[0m\n"
            "msf5 > use exploit/test\n"
            "\x1b[1;1R\x1b[1;1R"
            "msf5 exploit(test) > set RHOSTS 10.0.0.1\n"
            "[+] Exploit completed successfully\n"
            "[-] Some warning message\n"
            "[!] Error occurred\n"
            "[*] Started reverse TCP handler\n"
            "\n\n\n"
            "Regular output"
        )

        result = AnsiFilter.sanitize_msfconsole_output(msfconsole_output)

        # Should remove msfconsole prompts, status indicators, and ANSI codes
        # Should clean up excessive whitespace
        expected = (
            "Starting handler\n"
            "use exploit/test\n"
            "set RHOSTS 10.0.0.1\n"
            "Exploit completed successfully\n"
            "Some warning message\n"
            "Error occurred\n"
            "Regular output"
        )
        assert result == expected

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        # Test None input
        assert AnsiFilter.strip_ansi_codes(None) is None
        assert AnsiFilter.sanitize_terminal_output(None) is None

        # Test empty string
        assert AnsiFilter.sanitize_terminal_output("") == ""

        # Test string with only control characters
        only_controls = "\x1b[1;1R\x1b[2J\x07\x08"
        assert AnsiFilter.sanitize_terminal_output(only_controls) == ""

    def test_real_world_msfconsole_output(self):
        """Test with real-world msfconsole output patterns"""
        # Example of problematic output that was causing issues
        problematic_output = (
            "\x1b[1;1R\x1b[1;1R\x1b[1;1R\x1b[1;1R\x1b[1;1R"
            "msf6 > use exploit/unix/ftp/vsftpd_234_backdoor\n"
            "msf6 exploit(unix/ftp/vsftpd_234_backdoor) > set RHOSTS 10.10.10.3\n"
            "msf6 exploit(unix/ftp/vsftpd_234_backdoor) > run\n"
            "\x1b[31m[*] \x1b[0mStarted reverse TCP handler on 192.168.1.100:4444\n"
            "\x1b[32m[*] \x1b[0mExploit completed, but no session was created.\n"
        )

        result = AnsiFilter.sanitize_msfconsole_output(problematic_output)

        # Should be clean and readable
        expected = (
            "use exploit/unix/ftp/vsftpd_234_backdoor\n"
            "set RHOSTS 10.10.10.3\n"
            "run\n"
            "Exploit completed, but no session was created."
        )
        assert result == expected

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            # Test various ANSI color codes
            ("\x1b[30mBlack\x1b[0m", "Black"),
            ("\x1b[91mBright Red\x1b[0m", "Bright Red"),
            ("\x1b[48;5;214mOrange background\x1b[0m", "Orange background"),
            # Test cursor position reports (the main issue)
            ("\x1b[1;1R", ""),
            ("\x1b[25;80R", ""),
            ("Text\x1b[10;5RMore", "TextMore"),
            # Test mixed sequences
            ("\x1b[31m\x1b[1mBold Red\x1b[0m\x1b[1;1R", "Bold Red"),
        ],
    )
    def test_parametrized_filtering(self, input_text, expected):
        """Test various input patterns with expected outputs"""
        result = AnsiFilter.sanitize_terminal_output(input_text)
        assert result == expected
