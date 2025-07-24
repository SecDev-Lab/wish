"""Tests for CommandDispatcher job completion handling."""

from unittest.mock import AsyncMock, Mock

import pytest

from wish_cli.core.command_dispatcher import CommandDispatcher
from wish_cli.core.job_manager import JobInfo, JobStatus


@pytest.mark.asyncio
class TestCommandDispatcherJobCompletion:
    """Test job completion handling in CommandDispatcher."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for CommandDispatcher."""
        return {
            "ui_manager": Mock(),
            "state_manager": AsyncMock(),
            "session_manager": AsyncMock(),
            "conversation_manager": Mock(),
            "plan_generator": Mock(),
            "tool_executor": Mock(),
        }

    @pytest.fixture
    def command_dispatcher(self, mock_dependencies):
        """Create CommandDispatcher instance with mocks."""
        dispatcher = CommandDispatcher(**mock_dependencies)
        # Mock the parsers and detectors
        dispatcher.nmap_parser = Mock()
        dispatcher.vulnerability_detector = Mock()
        return dispatcher

    async def test_handle_job_completion_with_dict_result(self, command_dispatcher):
        """Test handling job completion when result is a dict."""
        # Create job info with dict result (common from job manager)
        job_info = JobInfo(
            job_id="test_job_001",
            description="Test nmap scan",
            status=JobStatus.COMPLETED,
            result={
                "success": True,
                "output": "Nmap scan report for 10.10.10.3\nHost is up.\nPORT   STATE SERVICE\n22/tcp open  ssh",
                "exit_code": 0,
                "tool": "nmap",
            },
            step_info={"tool_name": "nmap", "command": "nmap -p 22 10.10.10.3", "purpose": "Scan port 22"},
        )

        # Mock nmap parser
        command_dispatcher.nmap_parser.can_parse.return_value = True
        command_dispatcher.nmap_parser.parse_hosts.return_value = []

        # Should not raise an exception
        await command_dispatcher.handle_job_completion("test_job_001", job_info)

        # Verify parser was called with output string
        command_dispatcher.nmap_parser.can_parse.assert_called_once()
        call_arg = command_dispatcher.nmap_parser.can_parse.call_args[0][0]
        assert "Nmap scan report" in call_arg

    async def test_handle_job_completion_with_object_result(self, command_dispatcher):
        """Test handling job completion when result is an object with stdout."""
        # Create a mock result object (like ToolResult)
        result_obj = Mock()
        result_obj.success = True
        result_obj.stdout = "Nmap scan report for 10.10.10.3\nHost is up."
        result_obj.stderr = ""
        result_obj.exit_code = 0

        job_info = JobInfo(
            job_id="test_job_002",
            description="Test nmap scan",
            status=JobStatus.COMPLETED,
            result=result_obj,
            step_info={"tool_name": "nmap", "command": "nmap -p 22 10.10.10.3", "purpose": "Scan port 22"},
        )

        # Mock nmap parser
        command_dispatcher.nmap_parser.can_parse.return_value = True
        command_dispatcher.nmap_parser.parse_hosts.return_value = []

        # Should handle object format correctly
        await command_dispatcher.handle_job_completion("test_job_002", job_info)

        # Verify parser was called
        command_dispatcher.nmap_parser.can_parse.assert_called_once()

    async def test_update_from_nmap_result_dict_format(self, command_dispatcher):
        """Test _update_from_nmap_result with dict format."""
        # Dict format result (from job completion)
        result = {
            "success": True,
            "output": "Nmap scan report for 10.10.10.3\nPORT   STATE SERVICE\n22/tcp open  ssh",
            "exit_code": 0,
        }

        # Mock parser
        command_dispatcher.nmap_parser.can_parse.return_value = True
        mock_host = Mock()
        mock_host.ip_address = "10.10.10.3"
        mock_host.status = "up"
        mock_host.services = []
        command_dispatcher.nmap_parser.parse_hosts.return_value = [mock_host]
        command_dispatcher.vulnerability_detector.detect_vulnerabilities.return_value = []

        # Should not raise AttributeError
        await command_dispatcher._update_from_nmap_result(result)

        # Verify state was updated
        command_dispatcher.state_manager.update_hosts.assert_called_once()

    async def test_update_from_nmap_result_object_format(self, command_dispatcher):
        """Test _update_from_nmap_result with object format."""
        # Object format result (from direct tool execution)
        result = Mock()
        result.success = True
        result.stdout = "Nmap scan report for 10.10.10.3\nPORT   STATE SERVICE\n22/tcp open  ssh"

        # Mock parser
        command_dispatcher.nmap_parser.can_parse.return_value = True
        mock_host = Mock()
        mock_host.ip_address = "10.10.10.3"
        mock_host.status = "up"
        mock_host.services = []
        command_dispatcher.nmap_parser.parse_hosts.return_value = [mock_host]
        command_dispatcher.vulnerability_detector.detect_vulnerabilities.return_value = []

        # Should handle object format
        await command_dispatcher._update_from_nmap_result(result)

        # Verify state was updated
        command_dispatcher.state_manager.update_hosts.assert_called_once()

    async def test_handle_job_completion_with_failed_job(self, command_dispatcher):
        """Test handling job completion when job failed."""
        job_info = JobInfo(
            job_id="test_job_003",
            description="Test failed scan",
            status=JobStatus.FAILED,
            error="Command not found",
            step_info={"tool_name": "nmap", "command": "nmap -p 22 10.10.10.3"},
        )

        # Should not attempt to update state for failed job
        await command_dispatcher.handle_job_completion("test_job_003", job_info)

        # Verify state was not updated
        command_dispatcher.state_manager.update_hosts.assert_not_called()

    async def test_handle_job_completion_missing_step_info(self, command_dispatcher):
        """Test handling job completion when step_info is missing."""
        job_info = JobInfo(
            job_id="test_job_004",
            description="Test scan",
            status=JobStatus.COMPLETED,
            result={"success": True, "output": "scan output"},
            step_info=None,  # Missing step info
        )

        # Should handle gracefully
        await command_dispatcher.handle_job_completion("test_job_004", job_info)

        # Verify no state update attempted
        command_dispatcher.state_manager.update_hosts.assert_not_called()

    async def test_handle_job_completion_with_empty_result(self, command_dispatcher):
        """Test handling job completion when result is empty."""
        job_info = JobInfo(
            job_id="test_job_005",
            description="Test scan",
            status=JobStatus.COMPLETED,
            result=None,  # Empty result
            step_info={"tool_name": "nmap", "command": "nmap -p 22 10.10.10.3"},
        )

        # Should handle gracefully
        await command_dispatcher.handle_job_completion("test_job_005", job_info)

        # Verify no state update attempted
        command_dispatcher.state_manager.update_hosts.assert_not_called()
