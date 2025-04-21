"""Tests for the ActResult class."""

import pytest

from wish_models.command_result import ActResult


def test_act_result_creation():
    """Test creating an ActResult."""
    # Arrange
    command = "nmap -p- 10.10.10.40"
    exit_class = "TIMEOUT"
    exit_code = "1"
    log_summary = "timeout"

    # Act
    result = ActResult(
        command=command,
        exit_class=exit_class,
        exit_code=exit_code,
        log_summary=log_summary
    )

    # Assert
    assert result.command == command
    assert result.exit_class == exit_class
    assert result.exit_code == exit_code
    assert result.log_summary == log_summary


def test_act_result_from_dict():
    """Test creating an ActResult from a dictionary."""
    # Arrange
    data = {
        "command": "nmap -p- 10.10.10.40",
        "exit_class": "TIMEOUT",
        "exit_code": "1",
        "log_summary": "timeout"
    }

    # Act
    result = ActResult.from_dict(data)

    # Assert
    assert result.command == data["command"]
    assert result.exit_class == data["exit_class"]
    assert result.exit_code == data["exit_code"]
    assert result.log_summary == data["log_summary"]


def test_act_result_model_dump():
    """Test converting an ActResult to a dictionary."""
    # Arrange
    result = ActResult(
        command="nmap -p- 10.10.10.40",
        exit_class="TIMEOUT",
        exit_code="1",
        log_summary="timeout"
    )

    # Act
    data = result.model_dump()

    # Assert
    assert isinstance(data, dict)
    assert data["command"] == result.command
    assert data["exit_class"] == result.exit_class
    assert data["exit_code"] == result.exit_code
    assert data["log_summary"] == result.log_summary
