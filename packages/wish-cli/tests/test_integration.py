"""Integration tests for wish-cli package integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from wish_cli.core.exploit_engine import ExploitEngine

# Import basic components that should be available
from wish_cli.core.vulnerability_detector import VulnerabilityDetector


class TestPackageIntegration:
    """Package integration tests."""

    @pytest.fixture
    def mock_tool_executor(self):
        """Mock tool executor."""
        executor = MagicMock()
        executor.execute_command = AsyncMock()
        return executor

    @pytest.mark.asyncio
    async def test_exploit_engine_verification(self, mock_tool_executor):
        """Test exploit engine verification functionality."""
        # Mock successful verification
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "uid=0(root) gid=0(root) groups=0(root)"
        mock_result.stderr = ""

        mock_tool_executor.execute_command = AsyncMock(return_value=mock_result)

        # Test exploit engine
        engine = ExploitEngine(mock_tool_executor)
        result = await engine.verify_vulnerability("CVE-2007-2447", "10.10.10.3", "id")

        # Check result
        assert result["success"] is True
        assert result["verified"] is True
        assert result["cve_id"] == "CVE-2007-2447"
        assert result["target"] == "10.10.10.3"
        assert "uid=0(root)" in result["output"]

    def test_vulnerability_detector_patterns(self):
        """Test vulnerability detector patterns."""
        detector = VulnerabilityDetector()

        # Test pattern matching
        assert "CVE-2007-2447" in [v["cve"] for v in detector.vulnerability_patterns.values()]
        assert "CVE-2011-2523" in [v["cve"] for v in detector.vulnerability_patterns.values()]

    def test_exploit_engine_availability(self):
        """Test exploit engine availability."""
        engine = ExploitEngine(MagicMock())

        # Test available exploits
        available = engine.list_available_exploits()
        assert "CVE-2007-2447" in available
        assert "CVE-2011-2523" in available

        # Test exploit info
        info = engine.get_exploit_info("CVE-2007-2447")
        assert info is not None
        assert info["name"] == "Samba 3.0.20 - Remote Command Execution"
