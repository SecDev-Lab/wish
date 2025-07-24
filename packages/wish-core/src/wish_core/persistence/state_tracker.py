"""State change tracking for auto-save triggering."""

import logging

from wish_models import CollectedData, Finding, Host

from .auto_save import AutoSaveManager


class StateChangeTracker:
    """Tracks state changes and triggers auto-save when needed."""

    def __init__(self, auto_save_manager: AutoSaveManager) -> None:
        """Initialize state change tracker.

        Args:
            auto_save_manager: AutoSaveManager instance to notify of changes
        """
        self.auto_save_manager = auto_save_manager
        self.logger = logging.getLogger(__name__)

    def track_host_change(self, host: Host, operation: str) -> None:
        """Track changes to host information.

        Args:
            host: The Host object that changed
            operation: Description of the operation (e.g., "added", "updated")
        """
        self.logger.debug(f"Host {operation}: {host.ip_address} ({host.id})")
        self.auto_save_manager.mark_changes()

    def track_finding_change(self, finding: Finding, operation: str) -> None:
        """Track changes to findings.

        Args:
            finding: The Finding object that changed
            operation: Description of the operation (e.g., "added", "updated")
        """
        self.logger.debug(f"Finding {operation}: {finding.title} ({finding.id})")
        self.auto_save_manager.mark_changes()

    def track_data_collection(self, data: CollectedData, operation: str) -> None:
        """Track changes to collected data.

        Args:
            data: The CollectedData object that changed
            operation: Description of the operation (e.g., "added", "updated")
        """
        self.logger.debug(f"Data {operation}: {data.type} ({data.id})")
        self.auto_save_manager.mark_changes()

    def track_mode_change(self, old_mode: str, new_mode: str) -> None:
        """Track engagement mode changes.

        Args:
            old_mode: Previous engagement mode
            new_mode: New engagement mode
        """
        self.logger.debug(f"Mode changed: {old_mode} -> {new_mode}")
        self.auto_save_manager.mark_changes()

    def track_command_execution(self, command: str) -> None:
        """Track command execution.

        Args:
            command: The command that was executed
        """
        self.logger.debug(f"Command executed: {command}")
        self.auto_save_manager.mark_changes()

    def track_target_change(self, target_id: str, operation: str) -> None:
        """Track changes to targets.

        Args:
            target_id: ID of the target that changed
            operation: Description of the operation (e.g., "added", "updated", "removed")
        """
        self.logger.debug(f"Target {operation}: {target_id}")
        self.auto_save_manager.mark_changes()

    def track_session_change(self, change_type: str, details: str = "") -> None:
        """Track general session changes.

        Args:
            change_type: Type of change (e.g., "metadata_update", "state_reset")
            details: Additional details about the change
        """
        self.logger.debug(f"Session {change_type}: {details}")
        self.auto_save_manager.mark_changes()
