"""System information collection for wish-command-execution."""

import asyncio
import os
import platform
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Optional

from wish_models import Wish

from wish_command_execution.backend.base import Backend
from wish_command_execution.backend.bash import BashBackend
from wish_command_execution.backend.sliver import SliverBackend


@dataclass
class SystemInfo:
    """Class to store system information."""
    os_name: str
    os_version: str
    executables: List[str]
    architecture: Optional[str] = None
    hostname: Optional[str] = None
    username: Optional[str] = None


class SystemInfoCollector:
    """Base class to collect system information."""
    
    def __init__(self, backend: Backend):
        """Initialize the system information collector.
        
        Args:
            backend: Backend to use for command execution
        """
        self.backend = backend
        
    async def collect_system_info(self, wish: Wish) -> SystemInfo:
        """Collect system information.
        
        Args:
            wish: Wish object for information collection
            
        Returns:
            SystemInfo: Collected system information
        """
        # Platform-agnostic commands to get OS and version
        if self._is_windows():
            os_info_cmd = "systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\""
            executables_cmd = "powershell -Command \"Get-ChildItem -Path ($env:PATH.Split(';')) -Filter *.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName | Sort-Object -Unique\""
        else:
            os_info_cmd = "uname -a"
            executables_cmd = "echo $PATH | tr ':' '\\n' | xargs -I{} find {} -type f -executable 2>/dev/null | sort -u"
        
        # Execute commands and get results
        os_info = await self._execute_command(wish, os_info_cmd)
        executables = await self._execute_command(wish, executables_cmd)
        
        # Parse results and create SystemInfo object
        return self._parse_system_info(os_info, executables)
    
    def _is_windows(self) -> bool:
        """Check if the system is Windows.
        
        Returns:
            bool: True if the system is Windows, False otherwise
        """
        return platform.system().lower() == "windows"
    
    async def _execute_command(self, wish: Wish, command: str) -> str:
        """Execute a command and get the result.
        
        Args:
            wish: Wish object
            command: Command to execute
            
        Returns:
            str: Command execution result
        """
        raise NotImplementedError("Subclasses must implement _execute_command")
    
    def _parse_system_info(self, os_info: str, executables: str) -> SystemInfo:
        """Parse command execution results to create a SystemInfo object.
        
        Args:
            os_info: Command execution result for OS and version
            executables: Command execution result for executable files
            
        Returns:
            SystemInfo: Parsed system information
        """
        raise NotImplementedError("Subclasses must implement _parse_system_info")


class BashSystemInfoCollector(SystemInfoCollector):
    """System information collector for BashBackend."""
    
    async def _execute_command(self, wish: Wish, command: str) -> str:
        """Execute a command using Bash and get the result.
        
        Args:
            wish: Wish object
            command: Command to execute
            
        Returns:
            str: Command execution result
        """
        # Create temporary log files
        with tempfile.NamedTemporaryFile(mode='w+') as stdout_file, tempfile.NamedTemporaryFile(mode='w+') as stderr_file:
            # Execute command
            process = subprocess.run(
                command, 
                shell=True, 
                text=True, 
                stdout=stdout_file, 
                stderr=stderr_file
            )
            
            # Read result
            stdout_file.seek(0)
            return stdout_file.read()
    
    def _parse_system_info(self, os_info: str, executables: str) -> SystemInfo:
        """Parse command execution results in Bash environment.
        
        Args:
            os_info: Command execution result for OS and version
            executables: Command execution result for executable files
            
        Returns:
            SystemInfo: Parsed system information
        """
        if self._is_windows():
            # Parse Windows systeminfo output
            os_name = ""
            os_version = ""
            for line in os_info.splitlines():
                if "OS Name" in line:
                    os_name = line.split(":", 1)[1].strip()
                elif "OS Version" in line:
                    os_version = line.split(":", 1)[1].strip()
        else:
            # Parse uname -a output
            os_name = platform.system()
            os_version = platform.release()
        
        # Create list of executable files
        executables_list = executables.strip().split('\n') if executables.strip() else []
        
        return SystemInfo(
            os_name=os_name,
            os_version=os_version,
            executables=executables_list,
            architecture=platform.machine(),
            hostname=platform.node(),
            username=os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USERNAME', 'unknown')
        )


class SliverSystemInfoCollector(SystemInfoCollector):
    """System information collector for SliverBackend."""
    
    async def _execute_command(self, wish: Wish, command: str) -> str:
        """Execute a command using Sliver C2 and get the result.
        
        Args:
            wish: Wish object
            command: Command to execute
            
        Returns:
            str: Command execution result
        """
        # Connect to Sliver server if not already connected
        if hasattr(self.backend, '_connect'):
            await self.backend._connect()
        
        # Execute command using SliverBackend
        cmd_result = await self.backend.interactive_session.execute(command, [])
        
        # Return result as string
        if cmd_result.Stdout:
            return cmd_result.Stdout.decode('utf-8', errors='replace')
        return ""
    
    def _parse_system_info(self, os_info: str, executables: str) -> SystemInfo:
        """Parse command execution results in Sliver environment.
        
        Args:
            os_info: Command execution result for OS and version
            executables: Command execution result for executable files
            
        Returns:
            SystemInfo: Parsed system information
        """
        if self._is_windows():
            # Parse Windows systeminfo output
            os_name = ""
            os_version = ""
            for line in os_info.splitlines():
                if "OS Name" in line:
                    os_name = line.split(":", 1)[1].strip()
                elif "OS Version" in line:
                    os_version = line.split(":", 1)[1].strip()
        else:
            # Parse uname -a output
            parts = os_info.strip().split()
            if len(parts) >= 3:
                os_name = parts[0]  # Linux
                os_version = parts[2]  # 5.4.0-42-generic
            else:
                os_name = "Unknown"
                os_version = "Unknown"
        
        # Create list of executable files
        executables_list = executables.strip().split('\n') if executables.strip() else []
        
        # Get hostname and username (available from Sliver session)
        hostname = None
        username = None
        architecture = None
        
        # Get information from Sliver session if available
        if hasattr(self.backend, 'interactive_session'):
            session = self.backend.interactive_session
            if hasattr(session, 'Hostname'):
                hostname = session.Hostname
            if hasattr(session, 'Username'):
                username = session.Username
            if hasattr(session, 'Arch'):
                architecture = session.Arch
        
        return SystemInfo(
            os_name=os_name,
            os_version=os_version,
            executables=executables_list,
            architecture=architecture,
            hostname=hostname,
            username=username
        )


def create_system_info_collector(backend: Backend) -> SystemInfoCollector:
    """Create a system information collector for the backend.
    
    Args:
        backend: Backend to use for command execution
        
    Returns:
        SystemInfoCollector: System information collector
    """
    if isinstance(backend, BashBackend):
        return BashSystemInfoCollector(backend)
    elif isinstance(backend, SliverBackend):
        return SliverSystemInfoCollector(backend)
    else:
        raise ValueError(f"Unsupported backend type: {type(backend)}")
