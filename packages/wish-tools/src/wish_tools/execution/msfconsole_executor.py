"""
Specialized executor for msfconsole with PTY support
"""

import asyncio
import logging
import os
import pty
import select
import signal
import time
from pathlib import Path

from .ansi_filter import AnsiFilter

logger = logging.getLogger(__name__)


class MsfconsoleExecutor:
    """Specialized executor for msfconsole with proper TTY handling"""

    def __init__(self):
        """Initialize the msfconsole executor"""
        self.process: asyncio.subprocess.Process | None = None
        self.master_fd: int | None = None

    async def execute_msfconsole_command(
        self,
        command: str,
        timeout: int = 300,
        working_directory: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> tuple[str, str, int]:
        """
        Execute msfconsole command with proper PTY handling

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Add msfconsole-specific environment variables
        env.update(
            {
                "TERM": "xterm",
                "COLUMNS": "80",
                "LINES": "24",
                "MSF_DATABASE_CONFIG": "/dev/null",  # Disable database to avoid warnings
            }
        )

        # Validate working directory
        if working_directory:
            work_dir = Path(working_directory)
            if not work_dir.exists() or not work_dir.is_dir():
                raise ValueError(f"Invalid working directory: {working_directory}")

        logger.info(f"Executing msfconsole command with PTY: {command}")

        try:
            # Create PTY for msfconsole
            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd

            # Prepare msfconsole command
            # Use -n flag to suppress banner, -q for quiet mode
            msfconsole_cmd = f'msfconsole -n -q -x "{command}; exit"'

            # Create subprocess with PTY
            self.process = await asyncio.create_subprocess_shell(
                msfconsole_cmd,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=working_directory,
                env=env,
                preexec_fn=os.setsid,  # Create new session
            )

            # Close slave fd in parent process
            os.close(slave_fd)

            # Read output with timeout
            stdout_data = await self._read_pty_output(master_fd, timeout)

            # Wait for process to complete
            try:
                await asyncio.wait_for(self.process.wait(), timeout=10)
            except TimeoutError:
                # Force kill if still running
                await self._terminate_process()

            exit_code = self.process.returncode if self.process else -1

            # Clean up output
            clean_stdout = AnsiFilter.sanitize_msfconsole_output(stdout_data)

            logger.info(f"Msfconsole command completed with exit code: {exit_code}")
            return clean_stdout, "", exit_code

        except Exception as e:
            logger.error(f"Error executing msfconsole command: {e}", exc_info=True)
            await self._cleanup()
            raise

        finally:
            await self._cleanup()

    async def _read_pty_output(self, master_fd: int, timeout: int) -> str:
        """Read output from PTY with timeout"""
        output_buffer = bytearray()
        start_time = time.time()

        # Set non-blocking mode
        import fcntl

        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        while time.time() - start_time < timeout:
            try:
                # Use select to check for data availability
                ready, _, _ = select.select([master_fd], [], [], 0.1)

                if ready:
                    try:
                        data = os.read(master_fd, 4096)
                        if not data:
                            break  # EOF
                        output_buffer.extend(data)

                        # Check for msfconsole exit indicators
                        text = output_buffer.decode("utf-8", errors="replace")
                        if self._is_msfconsole_finished(text):
                            break

                    except OSError as e:
                        if e.errno == 11:  # EAGAIN - no data available
                            continue
                        else:
                            break

                # Check if process has terminated
                if self.process and self.process.returncode is not None:
                    # Read any remaining data
                    try:
                        remaining = os.read(master_fd, 4096)
                        if remaining:
                            output_buffer.extend(remaining)
                    except OSError:
                        pass
                    break

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.warning(f"Error reading PTY output: {e}")
                break

        return output_buffer.decode("utf-8", errors="replace")

    def _is_msfconsole_finished(self, output: str) -> bool:
        """Check if msfconsole has finished execution"""
        # Look for msfconsole exit indicators
        exit_indicators = [
            "Interrupt: use the 'exit' command to quit",
            "Thank you for using Metasploit",
            "Database connection isn't established",
            "Session",  # Session created or finished
        ]

        for indicator in exit_indicators:
            if indicator in output:
                return True

        # Check for common completion patterns
        if "Exploit completed" in output:
            return True

        if "Auxiliary module execution completed" in output:
            return True

        return False

    async def _terminate_process(self) -> None:
        """Terminate the msfconsole process"""
        if not self.process:
            return

        try:
            # Send SIGTERM to process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except TimeoutError:
                # Force kill
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                await self.process.wait()

        except (ProcessLookupError, OSError):
            # Process already terminated
            pass

    async def _cleanup(self) -> None:
        """Clean up resources"""
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

        if self.process:
            try:
                await self._terminate_process()
            except Exception as e:
                logger.debug(f"Error terminating process: {e}")
            self.process = None
