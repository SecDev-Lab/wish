import json
from pathlib import Path
from unittest.mock import patch

import pytest

from wish_models.command_result.command_result import CommandResult, parse_command_results_json
from wish_models.command_result.command_state import CommandState
from wish_models.test_factories.command_result_factory import CommandResultDoingFactory, CommandResultSuccessFactory
from wish_models.test_factories.log_files_factory import LogFilesFactory
from wish_models.utc_datetime import UtcDatetime


class TestCommandResult:
    def test_command_result_creation(self):
        now = UtcDatetime.now()
        data = {
            "num": 1,
            "command": "echo hello",
            "timeout_sec": 0,
            "exit_code": 0,
            "state": "SUCCESS",
            "log_summary": "Executed successfully",
            "log_files": {"stdout": "out.log", "stderr": "err.log"},
            "created_at": now,
            "finished_at": now,
        }
        cr = CommandResult.from_dict(data)
        assert cr.command == "echo hello"
        assert cr.timeout_sec == 0
        assert cr.exit_code == 0
        assert cr.state == CommandState.SUCCESS
        assert cr.log_summary == "Executed successfully"
        assert cr.log_files.stdout == Path("out.log")
        assert cr.log_files.stderr == Path("err.log")
        assert isinstance(cr.created_at, UtcDatetime)
        assert isinstance(cr.finished_at, UtcDatetime)

    @pytest.mark.parametrize(
        "command_result",
        [
            CommandResultDoingFactory.create(),
            CommandResultSuccessFactory.create(),
        ],
    )
    def test_to_json_and_from_json(self, command_result):
        json_str = command_result.to_json()
        cr2 = CommandResult.from_json(json_str)
        assert command_result == cr2

    def test_create(self):
        # Arrange
        num = 1
        command = "echo hello"
        log_files = LogFilesFactory.create()
        now = UtcDatetime.now()

        # Act
        with patch("wish_models.utc_datetime.UtcDatetime.now", return_value=now):
            result = CommandResult.create(num=num, command=command, log_files=log_files)

        # Assert
        assert result.num == num
        assert result.command == command
        assert result.state == CommandState.DOING
        assert result.log_files == log_files
        assert result.created_at == now
        assert result.timeout_sec is None
        assert result.exit_code is None
        assert result.log_summary is None
        assert result.finished_at is None

    def test_finish_success(self):
        """Test that finish method correctly updates a command result for success case."""
        # Arrange
        result = CommandResultDoingFactory.create()
        exit_code = 0
        state = CommandState.SUCCESS
        now = UtcDatetime.now()
        log_summary = "Command executed successfully"

        # Act
        with patch("wish_models.utc_datetime.UtcDatetime.now", return_value=now):
            result.finish(exit_code=exit_code, state=state, log_summary=log_summary)

        # Assert
        assert result.exit_code == exit_code
        assert result.state == state
        assert result.finished_at == now
        assert result.log_summary == log_summary

    def test_finish_failure(self):
        """Test that finish method correctly updates a command result for failure case."""
        # Arrange
        result = CommandResultDoingFactory.create()
        exit_code = 1
        state = CommandState.OTHERS
        now = UtcDatetime.now()
        log_summary = "Command failed with error"

        # Act
        with patch("wish_models.utc_datetime.UtcDatetime.now", return_value=now):
            result.finish(exit_code=exit_code, state=state, log_summary=log_summary)

        # Assert
        assert result.exit_code == exit_code
        assert result.state == state
        assert result.finished_at == now
        assert result.log_summary == log_summary

    def test_finish_cancelled(self):
        """Test that finish method correctly updates a command result for cancelled case."""
        # Arrange
        result = CommandResultDoingFactory.create()
        exit_code = -1
        state = CommandState.USER_CANCELLED
        now = UtcDatetime.now()
        log_summary = "Command was cancelled by user"

        # Act
        with patch("wish_models.utc_datetime.UtcDatetime.now", return_value=now):
            result.finish(exit_code=exit_code, state=state, log_summary=log_summary)

        # Assert
        assert result.exit_code == exit_code
        assert result.state == state
        assert result.finished_at == now
        assert result.log_summary == log_summary


def test_parse_command_results_json():
    data_list = [
        CommandResultDoingFactory.create().to_dict(),
        CommandResultSuccessFactory.create().to_dict(),
    ]
    json_str = json.dumps(data_list)
    results = parse_command_results_json(json_str)
    assert len(results) == 2
    assert results[0].command == data_list[0]["command"]
    assert results[1].command == data_list[1]["command"]
