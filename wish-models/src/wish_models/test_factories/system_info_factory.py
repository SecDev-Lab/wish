import os
import platform

import factory

from wish_models.system_info import SystemInfo


class SystemInfoFactory(factory.Factory):
    """Factory for creating SystemInfo instances for testing."""

    class Meta:
        model = SystemInfo

    os = "TestOS"
    arch = "x86_64"
    version = "1.0"
    hostname = "test-host"
    username = "test-user"
    uid = "1000"
    gid = "1000"
    pid = 12345

    @classmethod
    def create_from_local_system(cls) -> SystemInfo:
        """Create a SystemInfo instance from the local system."""
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

        return info
