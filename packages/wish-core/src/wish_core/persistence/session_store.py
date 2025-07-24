"""Session persistence management for wish-core."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from wish_models import EngagementState


class SessionStore:
    """Session persistence manager."""

    def __init__(self, base_path: str = "~/.wish") -> None:
        """Initialize session store with base directory."""
        self.base_path = Path(base_path).expanduser()
        self.sessions_dir = self.base_path / "sessions"
        self.archives_dir = self.sessions_dir / "archives"
        self.logger = logging.getLogger(__name__)

        # Create directories
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.archives_dir.mkdir(parents=True, exist_ok=True)

        self.current_session_file = self.sessions_dir / "current_session.json"
        self.session_history_file = self.sessions_dir / "session_history.json"

    async def save_current_session(self, engagement_state: EngagementState) -> None:
        """Save the current session to disk."""
        try:
            data = self._engagement_state_to_dict(engagement_state)

            # Write to temporary file first, then atomic move
            temp_file = self.current_session_file.with_suffix(".tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            temp_file.replace(self.current_session_file)

            self.logger.info(f"Session saved: {engagement_state.session_metadata.session_id}")

        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            raise

    async def load_current_session(self) -> EngagementState | None:
        """Load the current session from disk."""
        if not self.current_session_file.exists():
            return None

        try:
            with open(self.current_session_file, encoding="utf-8") as f:
                data = json.load(f)

            # Validate data structure
            if not self._validate_session_data(data):
                self.logger.warning("Invalid session data found, skipping load")
                return None

            return self._dict_to_engagement_state(data)

        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            # Backup corrupted file
            backup_file = self.current_session_file.with_suffix(
                f".corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.current_session_file.rename(backup_file)
            return None

    async def archive_session(self, engagement_state: EngagementState, custom_name: str | None = None) -> str:
        """Archive a session with optional custom name."""
        # Generate archive filename
        if custom_name:
            archive_name = f"{datetime.now().strftime('%Y-%m-%d')}_{custom_name}.json"
        else:
            session_name = engagement_state.name or "session"
            archive_name = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{session_name}.json"

        archive_path = self.archives_dir / archive_name

        # Prepare data for archiving
        data = self._engagement_state_to_dict(engagement_state)
        data["archived_at"] = datetime.now().isoformat()

        # Save archive file
        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        # Add to session history
        await self._add_to_history(engagement_state, str(archive_path))

        # Clear current session
        if self.current_session_file.exists():
            self.current_session_file.unlink()

        self.logger.info(f"Session archived: {archive_path}")
        return str(archive_path)

    async def list_archived_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List archived sessions with metadata."""
        archives = []

        for archive_file in self.archives_dir.glob("*.json"):
            try:
                with open(archive_file, encoding="utf-8") as f:
                    data = json.load(f)

                session_metadata = data.get("session_metadata", {})
                archives.append(
                    {
                        "file_path": str(archive_file),
                        "session_id": session_metadata.get("session_id"),
                        "engagement_name": data.get("name"),
                        "created_at": session_metadata.get("session_start"),
                        "last_activity": session_metadata.get("last_activity"),
                        "total_findings": session_metadata.get("total_findings", 0),
                        "current_mode": session_metadata.get("current_mode"),
                        "file_size": archive_file.stat().st_size,
                        "archived_at": data.get("archived_at"),
                    }
                )

            except Exception as e:
                self.logger.warning(f"Failed to read archive {archive_file}: {e}")

        # Sort by creation time, most recent first
        archives.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return archives[:limit]

    async def load_archived_session(self, archive_path: str) -> EngagementState | None:
        """Load an archived session from disk."""
        try:
            with open(archive_path, encoding="utf-8") as f:
                data = json.load(f)

            return self._dict_to_engagement_state(data)

        except Exception as e:
            self.logger.error(f"Failed to load archived session {archive_path}: {e}")
            return None

    async def cleanup_old_archives(self, max_age_days: int = 30, max_count: int = 100) -> None:
        """Clean up old archive files."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        archives = list(self.archives_dir.glob("*.json"))
        archives.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Delete old files
        for archive_file in archives:
            file_time = datetime.fromtimestamp(archive_file.stat().st_mtime)
            if file_time < cutoff_date:
                archive_file.unlink()
                self.logger.info(f"Deleted old archive: {archive_file}")

        # Enforce file count limit
        remaining_archives = [f for f in archives if f.exists()]
        if len(remaining_archives) > max_count:
            for archive_file in remaining_archives[max_count:]:
                archive_file.unlink()
                self.logger.info(f"Deleted excess archive: {archive_file}")

    def _validate_session_data(self, data: dict[str, Any]) -> bool:
        """Validate session data structure."""
        required_fields = ["session_metadata", "targets", "hosts", "findings", "collected_data"]
        return all(field in data for field in required_fields)

    def _engagement_state_to_dict(self, engagement_state: EngagementState) -> dict[str, Any]:
        """Convert EngagementState to serializable dictionary."""
        return {
            "id": engagement_state.id,
            "name": engagement_state.name,
            "created_at": engagement_state.created_at.isoformat(),
            "updated_at": engagement_state.updated_at.isoformat(),
            "session_metadata": {
                "session_id": engagement_state.session_metadata.session_id,
                "session_start": engagement_state.session_metadata.session_start.isoformat(),
                "last_activity": engagement_state.session_metadata.last_activity.isoformat(),
                "total_findings": engagement_state.session_metadata.total_findings,
                "current_mode": engagement_state.session_metadata.current_mode,
                "command_history": engagement_state.session_metadata.command_history,
            },
            "targets": {tid: target.model_dump() for tid, target in engagement_state.targets.items()},
            "hosts": {hid: host.model_dump() for hid, host in engagement_state.hosts.items()},
            "findings": {fid: finding.model_dump() for fid, finding in engagement_state.findings.items()},
            "collected_data": {did: data.model_dump() for did, data in engagement_state.collected_data.items()},
        }

    def _dict_to_engagement_state(self, data: dict[str, Any]) -> EngagementState:
        """Convert dictionary back to EngagementState."""
        from wish_models import CollectedData, Finding, Host, SessionMetadata, Target

        # Parse session metadata
        session_data = data["session_metadata"]
        session_metadata = SessionMetadata(
            session_id=session_data["session_id"],
            session_start=datetime.fromisoformat(session_data["session_start"]),
            last_activity=datetime.fromisoformat(session_data["last_activity"]),
            total_findings=session_data["total_findings"],
            current_mode=session_data["current_mode"],
            command_history=session_data["command_history"],
            engagement_name=session_data.get("engagement_name"),
            notes=session_data.get("notes"),
            total_commands=session_data.get("total_commands", 0),
            total_hosts_discovered=session_data.get("total_hosts_discovered", 0),
        )

        # Parse targets, hosts, findings, collected_data
        targets = {tid: Target.model_validate(target_data) for tid, target_data in data["targets"].items()}
        hosts = {hid: Host.model_validate(host_data) for hid, host_data in data["hosts"].items()}
        findings = {fid: Finding.model_validate(finding_data) for fid, finding_data in data["findings"].items()}
        collected_data = {
            did: CollectedData.model_validate(data_item) for did, data_item in data["collected_data"].items()
        }

        return EngagementState(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            session_metadata=session_metadata,
            targets=targets,
            hosts=hosts,
            findings=findings,
            collected_data=collected_data,
        )

    async def _add_to_history(self, engagement_state: EngagementState, archive_path: str) -> None:
        """Add session to history log."""
        history = []

        # Load existing history
        if self.session_history_file.exists():
            try:
                with open(self.session_history_file, encoding="utf-8") as f:
                    history = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load session history: {e}")

        # Add new entry
        history.append(
            {
                "session_id": engagement_state.session_metadata.session_id,
                "engagement_name": engagement_state.name,
                "archive_path": archive_path,
                "created_at": engagement_state.created_at.isoformat(),
                "total_findings": engagement_state.session_metadata.total_findings,
                "archived_at": datetime.now().isoformat(),
            }
        )

        # Limit history size
        if len(history) > 50:
            history = history[-50:]

        # Save updated history
        with open(self.session_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
