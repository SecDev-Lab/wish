"""Unit tests for the analyzer module."""

import pytest
from wish_log_analysis_api.core.analyzer import analyze_command_result
from wish_log_analysis_api.config import AnalyzerConfig
from wish_log_analysis_api.models import AnalyzeRequest
from wish_models.command_result import CommandResult
from wish_models.command_result.log_files import LogFiles
from wish_models.utc_datetime import UtcDatetime
from pathlib import Path
import tempfile
import os


@pytest.fixture
def sample_log_files():
    """Create sample log files for testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
        stdout_file.write("Sample stdout content")
        stdout_path = stdout_file.name
        
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
        stderr_file.write("Sample stderr content")
        stderr_path = stderr_file.name
        
    yield LogFiles(stdout=Path(stdout_path), stderr=Path(stderr_path))
    
    # Cleanup
    os.unlink(stdout_path)
    os.unlink(stderr_path)


@pytest.fixture
def sample_command_result(sample_log_files):
    """Create a sample command result for testing"""
    return CommandResult(
        num=1,
        command="ls -la",
        state="DOING",
        exit_code=0,
        log_files=sample_log_files,
        created_at=UtcDatetime.now(),
        finished_at=UtcDatetime.now()
    )


def test_analyze_command_result_with_custom_config(sample_command_result):
    """Test command result analysis with custom configuration"""
    # Create custom configuration
    config = AnalyzerConfig(
        openai_model="gpt-3.5-turbo",  # Use lightweight model for testing
    )
    
    # Create request
    request = AnalyzeRequest(command_result=sample_command_result)
    
    # Run analysis
    response = analyze_command_result(request, config=config)
    
    # Verify results
    assert response is not None
    assert response.analyzed_command_result is not None
    assert response.analyzed_command_result.log_summary is not None
    assert response.analyzed_command_result.state is not None


def test_analyze_command_result_with_default_config(sample_command_result):
    """Test command result analysis with default configuration"""
    # Create request
    request = AnalyzeRequest(command_result=sample_command_result)
    
    # Run analysis
    response = analyze_command_result(request)
    
    # Verify results
    assert response is not None
    assert response.analyzed_command_result is not None
    assert response.analyzed_command_result.log_summary is not None
    assert response.analyzed_command_result.state is not None


# TODO: Add tests with mocks to avoid actual API calls
