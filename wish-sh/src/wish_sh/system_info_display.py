"""System information display utilities."""

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from wish_models.system_info import SystemInfo


def display_system_info(info: SystemInfo, console: Console) -> None:
    """
    Display system information in a formatted way.

    Args:
        info: The system information to display
        console: The console to display on
    """
    # Basic system information table
    table = Table(title="System Information")

    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("OS", info.os)
    table.add_row("Architecture", info.arch)
    if info.version:
        table.add_row("Version", info.version)
    table.add_row("Hostname", info.hostname)
    table.add_row("Username", info.username)
    if info.uid:
        table.add_row("UID", info.uid)
    if info.gid:
        table.add_row("GID", info.gid)
    if info.pid:
        table.add_row("PID", str(info.pid))

    console.print(table)


def display_executables(collection, title: str, console: Console) -> None:
    """
    Display executables grouped by directory.

    Args:
        collection: The executable collection to display
        title: The title for the display
        console: The console to display on
    """
    if not collection or not collection.executables:
        console.print(f"[yellow]No {title.lower()} found.[/yellow]")
        return

    # Group executables by directory
    grouped = collection.group_by_directory()

    # Create a tree view
    tree = Tree(f"[bold]{title}[/bold] ({len(collection.executables)} files)")

    # Sort directories for consistent display
    for directory in sorted(grouped.keys()):
        dir_tree = tree.add(f"[blue]{directory}[/blue] ({len(grouped[directory])} files)")

        # Sort files within each directory
        for exe in sorted(grouped[directory], key=lambda x: x.filename):
            if exe.permissions:
                dir_tree.add(f"[green]{exe.filename}[/green] ({exe.permissions}, {exe.size} bytes)")
            else:
                dir_tree.add(f"[green]{exe.filename}[/green] ({exe.size} bytes)")

    console.print(tree)
