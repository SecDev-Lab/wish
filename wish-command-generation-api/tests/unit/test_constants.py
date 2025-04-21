"""Unit tests for the constants module."""

import pathlib
from unittest.mock import mock_open, patch

import pytest

from wish_command_generation_api import constants


@pytest.fixture
def mock_docs_dir():
    """Create a mock docs directory for testing."""
    return pathlib.Path(__file__).parent / "mock_docs"


def test_read_doc_file_exists():
    """Test reading a document file that exists."""
    # Arrange
    mock_content = "# Test Document\n\nThis is a test document."

    # Act
    with patch("builtins.open", mock_open(read_data=mock_content)) as mock_file:
        with patch("pathlib.Path.exists", return_value=True):
            result = constants._read_doc_file("test_doc.md")

    # Assert
    assert result == mock_content
    mock_file.assert_called_once()


def test_read_doc_file_not_exists():
    """Test reading a document file that does not exist."""
    # Arrange & Act
    with patch("pathlib.Path.exists", return_value=False):
        result = constants._read_doc_file("nonexistent_doc.md")

    # Assert
    assert result == ""


def test_dialog_avoidance_doc_content():
    """Test that DIALOG_AVOIDANCE_DOC contains the expected content."""
    # Assert
    assert "対話回避" in constants.DIALOG_AVOIDANCE_DOC
    assert "msfconsole" in constants.DIALOG_AVOIDANCE_DOC
    assert "smbclient" in constants.DIALOG_AVOIDANCE_DOC


def test_fast_alternative_doc_content():
    """Test that FAST_ALTERNATIVE_DOC contains the expected content."""
    # Assert
    assert "高速な代替コマンド" in constants.FAST_ALTERNATIVE_DOC
    assert "nmap" in constants.FAST_ALTERNATIVE_DOC
    assert "rustscan" in constants.FAST_ALTERNATIVE_DOC


def test_list_files_doc_content():
    """Test that LIST_FILES_DOC contains the expected content."""
    # Assert
    assert "リストファイル" in constants.LIST_FILES_DOC
    assert "ユーザーリスト" in constants.LIST_FILES_DOC
    assert "パスワードリスト" in constants.LIST_FILES_DOC


def test_divide_and_conquer_doc_content():
    """Test that DIVIDE_AND_CONQUER_DOC contains the expected content."""
    # Assert
    assert "分割統治" in constants.DIVIDE_AND_CONQUER_DOC
    assert "nmap -p-" in constants.DIVIDE_AND_CONQUER_DOC
    assert "nmap -p1-1000" in constants.DIVIDE_AND_CONQUER_DOC
