"""Integration tests for library usage."""

import pytest
from wish_log_analysis_api.core.analyzer import analyze_command_result
from wish_log_analysis_api.models import AnalyzeRequest
from wish_log_analysis_api.config import AnalyzerConfig
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.command_result.log_files import LogFiles
from wish_models.utc_datetime import UtcDatetime
from pathlib import Path
import tempfile
import os


@pytest.mark.integration
def test_end_to_end_analysis():
    """End-to-end library usage test"""
    # Create test log files
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
        stdout_file.write("Command executed successfully")
        stdout_path = stdout_file.name
        
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
        stderr_file.write("")
        stderr_path = stderr_file.name
    
    try:
        # Create command result
        log_files = LogFiles(stdout=Path(stdout_path), stderr=Path(stderr_path))
        command_result = CommandResult(
            num=1,
            command="echo 'test'",
            state=CommandState.DOING,
            exit_code=0,
            log_files=log_files,
            created_at=UtcDatetime.now(),
            finished_at=UtcDatetime.now()
        )
        
        # Create request
        request = AnalyzeRequest(command_result=command_result)
        
        # Run analysis
        response = analyze_command_result(request)
        
        # Verify results
        assert response is not None
        assert response.analyzed_command_result is not None
        assert response.analyzed_command_result.state == CommandState.SUCCESS
        assert response.analyzed_command_result.log_summary is not None
        assert "successfully" in response.analyzed_command_result.log_summary.lower()
    
    finally:
        # Cleanup
        os.unlink(stdout_path)
        os.unlink(stderr_path)


@pytest.mark.integration
def test_custom_config_integration():
    """Test library usage with custom configuration"""
    # Create test log files
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
        stdout_file.write("Error: command not found")
        stdout_path = stdout_file.name
        
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
        stderr_file.write("bash: unknown_command: command not found")
        stderr_path = stderr_file.name
    
    try:
        # Create command result
        log_files = LogFiles(stdout=Path(stdout_path), stderr=Path(stderr_path))
        command_result = CommandResult(
            num=1,
            command="unknown_command",
            state=CommandState.DOING,
            exit_code=127,
            log_files=log_files,
            created_at=UtcDatetime.now(),
            finished_at=UtcDatetime.now()
        )
        
        # Create request
        request = AnalyzeRequest(command_result=command_result)
        
        # Create custom configuration
        config = AnalyzerConfig(
            openai_model="gpt-3.5-turbo",  # Use lightweight model for testing
            langchain_tracing_v2=True
        )
        
        # Run analysis with custom configuration
        response = analyze_command_result(request, config=config)
        
        # Verify results
        assert response is not None
        assert response.analyzed_command_result is not None
        assert response.analyzed_command_result.state == CommandState.COMMAND_NOT_FOUND
        assert response.analyzed_command_result.log_summary is not None
        assert "not found" in response.analyzed_command_result.log_summary.lower()
    
    finally:
        # Cleanup
        os.unlink(stdout_path)
        os.unlink(stderr_path)
