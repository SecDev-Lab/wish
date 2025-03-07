from pathlib import Path

from wish_sh.settings import Settings


class WishPaths:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.history_path = Path(settings.WISH_HOME) / "history.jsonl"

    def ensure_directories(self):
        """Ensure all required directories exist."""
        wish_home = Path(self.settings.WISH_HOME)
        wish_home.mkdir(parents=True, exist_ok=True)

        # Ensure history file exists
        if not self.history_path.exists():
            with open(self.history_path, "w") as _f:
                pass

    def get_wish_dir(self, wish_id: str) -> Path:
        """Get the directory for a specific wish."""
        return Path(self.settings.WISH_HOME) / "w" / wish_id

    def create_command_log_dirs(self, wish_id: str) -> Path:
        """Create log directories for commands of a wish."""
        cmd_log_dir = self.get_wish_dir(wish_id) / "c" / "log"
        cmd_log_dir.mkdir(parents=True, exist_ok=True)
        return cmd_log_dir
