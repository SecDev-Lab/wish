"""Tests for the SystemInfoCollector class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_models.executable_collection import ExecutableCollection
from wish_models.system_info import SystemInfo

from wish_command_execution.system_info import SystemInfoCollector


class TestSystemInfoCollector:
    """Test cases for the SystemInfoCollector class."""

    @pytest.mark.asyncio
    async def test_collect_basic_info_from_session(self):
        """Test collecting basic system information from a session."""
        # Create a mock session
        mock_session = MagicMock()
        mock_session.os = "Linux"
        mock_session.arch = "x86_64"
        mock_session.version = "5.10.0"
        mock_session.hostname = "test-host"
        mock_session.username = "test-user"
        mock_session.uid = "1000"
        mock_session.gid = "1000"
        mock_session.pid = 12345

        # Call the method
        info = await SystemInfoCollector.collect_basic_info_from_session(mock_session)

        # Verify the result
        assert isinstance(info, SystemInfo)
        assert info.os == "Linux"
        assert info.arch == "x86_64"
        assert info.version == "5.10.0"
        assert info.hostname == "test-host"
        assert info.username == "test-user"
        assert info.uid == "1000"
        assert info.gid == "1000"
        assert info.pid == 12345

    @pytest.mark.asyncio
    async def test_collect_executables_from_session_linux(self):
        """Test collecting executables from a Linux session."""
        # Create a mock session
        mock_session = MagicMock()
        mock_session.os = "linux"

        # Mock the execute method to return a list of executables
        mock_result = MagicMock()
        mock_result.Stdout = b"/usr/bin/python\n/usr/bin/bash\n"

        # Mock the ls result for each executable
        mock_ls_result1 = MagicMock()
        mock_ls_result1.Stdout = b"-rwxr-xr-x 12345 /usr/bin/python\n"

        mock_ls_result2 = MagicMock()
        mock_ls_result2.Stdout = b"-rwxr-xr-x 54321 /usr/bin/bash\n"

        # Set up the execute method to return different results based on the command
        async def mock_execute(cmd, args):
            if "which" in cmd:
                return mock_result
            elif "python" in cmd:
                return mock_ls_result1
            elif "bash" in cmd:
                return mock_ls_result2
            return MagicMock(Stdout=b"")

        mock_session.execute = AsyncMock(side_effect=mock_execute)

        # Call the method
        collection = await SystemInfoCollector.collect_executables_from_session(mock_session)

        # Verify the result
        assert isinstance(collection, ExecutableCollection)
        assert len(collection.executables) == 2

        # Check the first executable
        assert collection.executables[0].path == "/usr/bin/python"
        assert collection.executables[0].size == 12345
        assert collection.executables[0].permissions == "-rwxr-xr-x"

        # Check the second executable
        assert collection.executables[1].path == "/usr/bin/bash"
        assert collection.executables[1].size == 54321
        assert collection.executables[1].permissions == "-rwxr-xr-x"

    @pytest.mark.asyncio
    async def test_collect_executables_from_session_windows(self):
        """Test collecting executables from a Windows session."""
        # Create a mock session
        mock_session = MagicMock()
        mock_session.os = "windows"

        # Mock the execute method to return a list of executables
        mock_result = MagicMock()
        mock_result.Stdout = b"C:\\Windows\\System32\\cmd.exe,12345\nC:\\Windows\\System32\\powershell.exe,54321\n"

        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        collection = await SystemInfoCollector.collect_executables_from_session(mock_session)

        # Verify the result
        assert isinstance(collection, ExecutableCollection)
        assert len(collection.executables) == 2

        # Check the first executable
        assert collection.executables[0].path == "C:\\Windows\\System32\\cmd.exe"
        assert collection.executables[0].size == 12345

        # Check the second executable
        assert collection.executables[1].path == "C:\\Windows\\System32\\powershell.exe"
        assert collection.executables[1].size == 54321

    @pytest.mark.asyncio
    async def test_collect_from_session(self):
        """Test collecting both system info and executables from a session."""
        # Create a mock session
        mock_session = MagicMock()
        mock_session.os = "Linux"
        mock_session.arch = "x86_64"
        mock_session.version = "5.10.0"
        mock_session.hostname = "test-host"
        mock_session.username = "test-user"
        mock_session.uid = "1000"
        mock_session.gid = "1000"
        mock_session.pid = 12345

        # Mock the execute method to return a list of executables
        mock_result = MagicMock()
        mock_result.Stdout = b"/usr/bin/python\n"

        # Mock the ls result
        mock_ls_result = MagicMock()
        mock_ls_result.Stdout = b"-rwxr-xr-x 12345 /usr/bin/python\n"

        # Set up the execute method
        async def mock_execute(cmd, args):
            if "which" in cmd:
                return mock_result
            elif "ls" in cmd:
                return mock_ls_result
            return MagicMock(Stdout=b"")

        mock_session.execute = AsyncMock(side_effect=mock_execute)

        # Call the method
        info, collection = await SystemInfoCollector.collect_from_session(mock_session)

        # Verify the system info
        assert isinstance(info, SystemInfo)
        assert info.os == "Linux"
        assert info.arch == "x86_64"
        assert info.version == "5.10.0"
        assert info.hostname == "test-host"
        assert info.username == "test-user"
        assert info.uid == "1000"
        assert info.gid == "1000"
        assert info.pid == 12345

        # Verify the executables
        assert isinstance(collection, ExecutableCollection)
        assert len(collection.executables) == 1
        assert collection.executables[0].path == "/usr/bin/python"
        assert collection.executables[0].size == 12345
        assert collection.executables[0].permissions == "-rwxr-xr-x"

    def test_collect_local_system_info(self):
        """Test collecting system information from the local system."""
        # This is a bit harder to test deterministically, so we'll just verify
        # that it returns a SystemInfo object with some basic properties set
        with patch('platform.system', return_value='Linux'), \
             patch('platform.machine', return_value='x86_64'), \
             patch('platform.version', return_value='5.10.0'), \
             patch('platform.node', return_value='test-host'), \
             patch('os.getlogin', return_value='test-user'), \
             patch('os.getpid', return_value=12345), \
             patch('os.getuid', return_value=1000), \
             patch('os.getgid', return_value=1000), \
             patch.object(
                 SystemInfoCollector,
                 '_collect_local_path_executables',
                 return_value=ExecutableCollection()
             ), \
             patch.object(
                 SystemInfoCollector,
                 '_collect_local_system_executables',
                 return_value=ExecutableCollection()
             ):

            info = SystemInfoCollector.collect_local_system_info(collect_system_executables=True)

            # Verify the basic system info
            assert isinstance(info, SystemInfo)
            assert info.os == 'Linux'
            assert info.arch == 'x86_64'
            assert info.version == '5.10.0'
            assert info.hostname == 'test-host'
            assert info.username == 'test-user'
            assert info.pid == 12345
            assert info.uid == '1000'
            assert info.gid == '1000'

            # Note: We no longer check for path_executables and system_executables
            # as these fields were removed when we split the models
