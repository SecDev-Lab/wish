"""Tests for the SystemInfo model."""

from wish_models.system_info import SystemInfo
from wish_models.test_factories.system_info_factory import SystemInfoFactory


class TestSystemInfo:
    """Test cases for the SystemInfo model."""

    def test_system_info_creation(self):
        """Test that a SystemInfo instance can be created with required fields."""
        # Test with minimum required fields
        info = SystemInfo(
            os="Linux",
            arch="x86_64",
            hostname="test-host",
            username="test-user"
        )

        assert info.os == "Linux"
        assert info.arch == "x86_64"
        assert info.hostname == "test-host"
        assert info.username == "test-user"
        assert info.version is None
        assert info.uid is None
        assert info.gid is None
        assert info.pid is None

    def test_system_info_with_all_fields(self):
        """Test that a SystemInfo instance can be created with all fields."""
        info = SystemInfo(
            os="Linux",
            arch="x86_64",
            version="5.10.0",
            hostname="test-host",
            username="test-user",
            uid="1000",
            gid="1000",
            pid=12345
        )

        assert info.os == "Linux"
        assert info.arch == "x86_64"
        assert info.version == "5.10.0"
        assert info.hostname == "test-host"
        assert info.username == "test-user"
        assert info.uid == "1000"
        assert info.gid == "1000"
        assert info.pid == 12345

    def test_system_info_factory(self):
        """Test that SystemInfoFactory creates valid instances."""
        # Test default factory
        info = SystemInfoFactory()

        assert info.os == "TestOS"
        assert info.arch == "x86_64"
        assert info.version == "1.0"
        assert info.hostname == "test-host"
        assert info.username == "test-user"
        assert info.uid == "1000"
        assert info.gid == "1000"
        assert info.pid == 12345

    def test_system_info_factory_with_custom_values(self):
        """Test that SystemInfoFactory can create instances with custom values."""
        info = SystemInfoFactory(
            os="CustomOS",
            arch="arm64",
            version="2.0",
            hostname="custom-host",
            username="custom-user"
        )

        assert info.os == "CustomOS"
        assert info.arch == "arm64"
        assert info.version == "2.0"
        assert info.hostname == "custom-host"
        assert info.username == "custom-user"
        # These should still have the default values
        assert info.uid == "1000"
        assert info.gid == "1000"
        assert info.pid == 12345
