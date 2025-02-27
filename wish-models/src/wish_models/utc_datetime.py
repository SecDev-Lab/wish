from datetime import datetime, timezone

from pydantic import BaseModel, model_serializer, model_validator


class UtcDatetime(BaseModel):
    """UTC datetime, with ISO 8601 serialization."""

    v: datetime

    def __init__(self, v: datetime):
        """Convert to, or set UTC timezone."""
        if v.tzinfo is None or v.tzinfo.utcoffset(None) is None:
            v = v.replace(tzinfo=timezone.utc)

        # Drop microseconds
        v = v.replace(microsecond=0)

        super().__init__(v=v)

    def __str__(self) -> str:
        return self.serialize()

    @model_validator(mode="before")
    def validate_v(cls, value: str | datetime | dict) -> dict:
        if isinstance(value, str):
            v_ = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            v = v_.replace(tzinfo=timezone.utc)
            return {"v": v}
        elif isinstance(value, datetime):
            v = value.replace(tzinfo=timezone.utc)
            return {"v": v}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError(f"Unexpected type value: {value}")

    @model_serializer
    def serialize(self) -> str:
        return self.v.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def now(cls) -> "UtcDatetime":
        dt = datetime.now(tz=timezone.utc)
        dt_no_microsec = dt.replace(microsecond=0)
        return cls(v=dt_no_microsec)
