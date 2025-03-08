"""System information collector."""

import os
import platform
import subprocess
from typing import Tuple

from wish_models.executable_collection import ExecutableCollection
from wish_models.system_info import SystemInfo


class SystemInfoCollector:
    """Collector for system information."""

    @staticmethod
    async def collect_basic_info_from_session(session) -> SystemInfo:
        """
        Collect basic system information from a Sliver session.
        
        Args:
            session: Sliver InteractiveSession object
            
        Returns:
            SystemInfo: Collected basic system information
        """
        # Basic information collection
        info = SystemInfo(
            os=session.os,
            arch=session.arch,
            version=session.version,
            hostname=session.hostname,
            username=session.username,
            uid=session.uid,
            gid=session.gid,
            pid=session.pid
        )
        return info

    @staticmethod
    async def collect_executables_from_session(session, collect_system_executables: bool = False) -> ExecutableCollection:
        """
        Collect executable files information from a Sliver session.
        
        Args:
            session: Sliver InteractiveSession object
            collect_system_executables: Whether to collect executables from the entire system
            
        Returns:
            ExecutableCollection: Collection of executables
        """
        try:
            # Collect executables in PATH
            path_executables = await SystemInfoCollector._collect_path_executables(session)

            # Optionally collect system-wide executables
            if collect_system_executables:
                system_executables = await SystemInfoCollector._collect_system_executables(session)

                # Merge system executables into path executables
                for exe in system_executables.executables:
                    path_executables.executables.append(exe)

            return path_executables
        except Exception:
            # Return empty collection on error
            return ExecutableCollection()

    @staticmethod
    async def collect_from_session(session, collect_system_executables: bool = False) -> Tuple[SystemInfo, ExecutableCollection]:
        """
        Collect both system information and executables from a Sliver session.
        
        Args:
            session: Sliver InteractiveSession object
            collect_system_executables: Whether to collect executables from the entire system
            
        Returns:
            Tuple[SystemInfo, ExecutableCollection]: Collected system information and executables
        """
        # Collect basic system information
        info = await SystemInfoCollector.collect_basic_info_from_session(session)

        # Collect executables
        executables = await SystemInfoCollector.collect_executables_from_session(session, collect_system_executables)

        return info, executables

    @staticmethod
    async def _collect_path_executables(session) -> ExecutableCollection:
        """
        Execute commands to collect executables in PATH.
        
        Args:
            session: Sliver InteractiveSession object
            
        Returns:
            ExecutableCollection: Collection of executables in PATH
        """
        os_type = session.os.lower()
        collection = ExecutableCollection()

        if "linux" in os_type or "darwin" in os_type:
            # より単純なコマンドを使用
            cmd = "which ls cat grep find 2>/dev/null"

            # 結果を取得後、各ファイルの詳細情報を取得
            result = await session.execute(cmd, [])

            if result.Stdout:
                files = result.Stdout.decode('utf-8', errors='replace').splitlines()

                # 各ファイルの詳細情報を取得
                for file_path in files:
                    if not file_path.strip():
                        continue

                    # ファイルの詳細情報を取得
                    ls_cmd = f"ls -la \"{file_path}\" 2>/dev/null | awk '{{print $1,$5,$9}}'"
                    ls_result = await session.execute(ls_cmd, [])

                    if ls_result.Stdout:
                        ls_output = ls_result.Stdout.decode('utf-8', errors='replace').strip()
                        parts = ls_output.split(None, 2)
                        if len(parts) >= 3:
                            permissions, size_str, path = parts
                            try:
                                size = int(size_str)
                            except ValueError:
                                size = None
                            collection.add_executable(path, size, permissions)

                return collection

            # 以下は元のコマンドをフォールバックとして保持
            cmd = "echo $PATH | tr ':' '\\n' | xargs -I {} find {} -type f -executable -not -path \"*/\\.*\" 2>/dev/null"
            if "darwin" in os_type:
                cmd = "echo $PATH | tr ':' '\\n' | xargs -I {} find {} -type f -perm +111 -not -path \"*/\\.*\" 2>/dev/null"

            # Add size and permissions
            cmd += " | xargs -I {} sh -c 'ls -la \"{}\" | awk \"{ print \\$1,\\$5,\\$9 }\"'"
        elif "windows" in os_type:
            cmd = "$env:path -split ';' | ForEach-Object { Get-ChildItem -Path $_ -Include *.exe,*.bat,*.cmd -ErrorAction SilentlyContinue | Select-Object FullName,Length | ForEach-Object { $_.FullName + \",\" + $_.Length } }"
        else:
            return collection  # Empty collection for unknown OS

        # Execute command
        result = await session.execute(cmd, [])

        # Parse results
        if result.Stdout:
            stdout = result.Stdout.decode('utf-8', errors='replace')

            for line in stdout.splitlines():
                if not line.strip():
                    continue

                if "linux" in os_type or "darwin" in os_type:
                    parts = line.strip().split(None, 2)
                    if len(parts) >= 3:
                        permissions, size_str, path = parts
                        try:
                            size = int(size_str)
                        except ValueError:
                            size = None
                        collection.add_executable(path, size, permissions)
                elif "windows" in os_type:
                    parts = line.strip().split(',', 1)
                    if len(parts) >= 2:
                        path, size_str = parts
                        try:
                            size = int(size_str)
                        except ValueError:
                            size = None
                        collection.add_executable(path, size)

        return collection

    @staticmethod
    async def _collect_system_executables(session) -> ExecutableCollection:
        """
        Execute commands to collect system-wide executables.
        
        Args:
            session: Sliver InteractiveSession object
            
        Returns:
            ExecutableCollection: Collection of system-wide executables
        """
        os_type = session.os.lower()
        collection = ExecutableCollection()

        if "linux" in os_type:
            # This command can take a long time, so we limit to common executable directories
            cmd = "find /bin /sbin /usr/bin /usr/sbin /usr/local/bin /usr/local/sbin -type f -executable -not -path \"*/\\.*\" 2>/dev/null | xargs -I {} sh -c 'ls -la \"{}\" | awk \"{ print \\$1,\\$5,\\$9 }\"'"
        elif "darwin" in os_type:
            cmd = "find /bin /sbin /usr/bin /usr/sbin /usr/local/bin /usr/local/sbin -type f -perm +111 -not -path \"*/\\.*\" 2>/dev/null | xargs -I {} sh -c 'ls -la \"{}\" | awk \"{ print \\$1,\\$5,\\$9 }\"'"
        elif "windows" in os_type:
            cmd = "Get-ChildItem -Path C:\\Windows\\System32,C:\\Windows,C:\\Windows\\System32\\WindowsPowerShell\\v1.0 -Include *.exe,*.bat,*.cmd -Recurse -ErrorAction SilentlyContinue | Select-Object FullName,Length | ForEach-Object { $_.FullName + \",\" + $_.Length }"
        else:
            return collection  # Empty collection for unknown OS

        # Execute command
        result = await session.execute(cmd, [])

        # Parse results (same parsing logic as _collect_path_executables)
        if result.Stdout:
            stdout = result.Stdout.decode('utf-8', errors='replace')

            for line in stdout.splitlines():
                if not line.strip():
                    continue

                if "linux" in os_type or "darwin" in os_type:
                    parts = line.strip().split(None, 2)
                    if len(parts) >= 3:
                        permissions, size_str, path = parts
                        try:
                            size = int(size_str)
                        except ValueError:
                            size = None
                        collection.add_executable(path, size, permissions)
                elif "windows" in os_type:
                    parts = line.strip().split(',', 1)
                    if len(parts) >= 2:
                        path, size_str = parts
                        try:
                            size = int(size_str)
                        except ValueError:
                            size = None
                        collection.add_executable(path, size)

        return collection

    @staticmethod
    def collect_local_system_info(collect_system_executables: bool = False) -> SystemInfo:
        """
        Collect system information from the local system.
        
        Args:
            collect_system_executables: Whether to collect executables from the entire system
            
        Returns:
            SystemInfo: Collected system information
        """
        # Basic information
        system = platform.system()
        info = SystemInfo(
            os=system,
            arch=platform.machine(),
            version=platform.version(),
            hostname=platform.node(),
            username=os.getlogin(),
            pid=os.getpid()
        )

        # Add UID and GID for Unix-like systems
        if system != "Windows":
            info.uid = str(os.getuid())
            info.gid = str(os.getgid())

        # Collect executables in PATH
        # Note: We don't set path_executables and system_executables directly on the SystemInfo object
        # as these fields were removed when we split the models
        path_executables = SystemInfoCollector._collect_local_path_executables()

        # Optionally collect system-wide executables
        if collect_system_executables:
            system_executables = SystemInfoCollector._collect_local_system_executables()

        return info

    @staticmethod
    def _collect_local_path_executables() -> ExecutableCollection:
        """
        Collect executables in PATH from the local system.
        
        Returns:
            ExecutableCollection: Collection of executables in PATH
        """
        collection = ExecutableCollection()
        system = platform.system()

        # Get PATH directories
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)

        for directory in path_dirs:
            if not os.path.isdir(directory):
                continue

            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)

                # Check if it's an executable
                if system == "Windows":
                    if filename.lower().endswith((".exe", ".bat", ".cmd")) and os.path.isfile(filepath):
                        size = os.path.getsize(filepath)
                        collection.add_executable(filepath, size)
                else:
                    if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                        size = os.path.getsize(filepath)
                        # Get permissions string (similar to ls -l)
                        try:
                            permissions = subprocess.check_output(
                                ["ls", "-la", filepath],
                                stderr=subprocess.DEVNULL,
                                universal_newlines=True
                            ).strip().split(None, 1)[0]
                        except (subprocess.SubprocessError, IndexError):
                            permissions = None

                        collection.add_executable(filepath, size, permissions)

        return collection

    @staticmethod
    def _collect_local_system_executables() -> ExecutableCollection:
        """
        Collect system-wide executables from the local system.
        
        Returns:
            ExecutableCollection: Collection of system-wide executables
        """
        collection = ExecutableCollection()
        system = platform.system()

        if system == "Windows":
            # Common Windows executable directories
            dirs_to_check = [
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32"),
                os.environ.get("SystemRoot", "C:\\Windows"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "WindowsPowerShell", "v1.0")
            ]

            for directory in dirs_to_check:
                if not os.path.isdir(directory):
                    continue

                for root, _, files in os.walk(directory):
                    for filename in files:
                        if filename.lower().endswith((".exe", ".bat", ".cmd")):
                            filepath = os.path.join(root, filename)
                            try:
                                size = os.path.getsize(filepath)
                                collection.add_executable(filepath, size)
                            except (OSError, IOError):
                                pass  # Skip files we can't access
        else:
            # Common Unix-like executable directories
            dirs_to_check = [
                "/bin", "/sbin", "/usr/bin", "/usr/sbin",
                "/usr/local/bin", "/usr/local/sbin"
            ]

            for directory in dirs_to_check:
                if not os.path.isdir(directory):
                    continue

                for root, _, files in os.walk(directory):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                            try:
                                size = os.path.getsize(filepath)
                                # Get permissions string
                                try:
                                    permissions = subprocess.check_output(
                                        ["ls", "-la", filepath],
                                        stderr=subprocess.DEVNULL,
                                        universal_newlines=True
                                    ).strip().split(None, 1)[0]
                                except (subprocess.SubprocessError, IndexError):
                                    permissions = None

                                collection.add_executable(filepath, size, permissions)
                            except (OSError, IOError):
                                pass  # Skip files we can't access

        return collection
