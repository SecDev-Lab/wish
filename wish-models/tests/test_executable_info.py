"""Tests for the ExecutableInfo model."""

from wish_models.executable_info import ExecutableInfo
from wish_models.test_factories.executable_info_factory import ExecutableInfoFactory


class TestExecutableInfo:
    """Test cases for the ExecutableInfo model."""

    def test_executable_info_creation(self):
        """Test that an ExecutableInfo instance can be created with required fields."""
        # Test with minimum required fields
        info = ExecutableInfo(path="/usr/bin/python")

        assert info.path == "/usr/bin/python"
        assert info.size is None
        assert info.permissions is None

    def test_executable_info_with_all_fields(self):
        """Test that an ExecutableInfo instance can be created with all fields."""
        info = ExecutableInfo(
            path="/usr/bin/python",
            size=12345,
            permissions="rwxr-xr-x"
        )

        assert info.path == "/usr/bin/python"
        assert info.size == 12345
        assert info.permissions == "rwxr-xr-x"

    def test_directory_property(self):
        """Test that the directory property returns the correct directory."""
        info = ExecutableInfo(path="/usr/bin/python")
        assert info.directory == "/usr/bin"

        info = ExecutableInfo(path="/home/user/scripts/test.sh")
        assert info.directory == "/home/user/scripts"

    def test_filename_property(self):
        """Test that the filename property returns the correct filename."""
        info = ExecutableInfo(path="/usr/bin/python")
        assert info.filename == "python"

        info = ExecutableInfo(path="/home/user/scripts/test.sh")
        assert info.filename == "test.sh"

    def test_executable_info_factory(self):
        """Test that ExecutableInfoFactory creates valid instances."""
        # Test default factory
        info = ExecutableInfoFactory()

        assert info.path == "/usr/bin/test-executable"
        assert info.size == 12345
        assert info.permissions == "rwxr-xr-x"

    def test_executable_info_factory_with_custom_values(self):
        """Test that ExecutableInfoFactory can create instances with custom values."""
        info = ExecutableInfoFactory(
            path="/usr/local/bin/custom-executable",
            size=54321,
            permissions="rwxrwxr-x"
        )

        assert info.path == "/usr/local/bin/custom-executable"
        assert info.size == 54321
        assert info.permissions == "rwxrwxr-x"

    def test_create_with_directory(self):
        """Test that create_with_directory creates a valid instance."""
        info = ExecutableInfoFactory.create_with_directory(
            directory="/usr/local/bin",
            filename="custom-executable",
            size=54321,
            permissions="rwxrwxr-x"
        )

        assert info.path == "/usr/local/bin/custom-executable"
        assert info.size == 54321
        assert info.permissions == "rwxrwxr-x"
        assert info.directory == "/usr/local/bin"
        assert info.filename == "custom-executable"
