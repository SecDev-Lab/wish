"""Utility functions for log handling."""

from wish_models import LogFiles


def summarize_log(log_files: LogFiles) -> str:
    """Generate a simple summary of command logs.

    Args:
        log_files: The log files to summarize.

    Returns:
        A summary of the logs.
    """
    summary = []

    # Read stdout
    try:
        with open(log_files.stdout, "r") as f:
            stdout_content = f.read().strip()
            if stdout_content:
                lines = stdout_content.split("\n")
                if len(lines) > 10:
                    summary.append(f"Standard output: {len(lines)} lines")
                    summary.append("First few lines:")
                    summary.extend(lines[:3])
                    summary.append("...")
                    summary.extend(lines[-3:])
                else:
                    summary.append("Standard output:")
                    summary.extend(lines)
            else:
                summary.append("Standard output: <empty>")
    except FileNotFoundError:
        summary.append("Standard output: <file not found>")

    # Read stderr
    try:
        with open(log_files.stderr, "r") as f:
            stderr_content = f.read().strip()
            if stderr_content:
                lines = stderr_content.split("\n")
                if len(lines) > 5:
                    summary.append(f"Standard error: {len(lines)} lines")
                    summary.append("First few lines:")
                    summary.extend(lines[:3])
                    summary.append("...")
                else:
                    summary.append("Standard error:")
                    summary.extend(lines)

    except FileNotFoundError:
        pass  # Don't mention if stderr is empty or missing

    return "\n".join(summary)
