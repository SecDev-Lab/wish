from pathlib import Path

from pydantic import BaseModel, model_serializer


class LogFiles(BaseModel):
    stdout: Path
    stderr: Path

    @model_serializer
    def serialize(self) -> dict:
        """Serialize Path to str."""
        return {"stdout": str(self.stdout), "stderr": str(self.stderr)}
