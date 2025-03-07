from datetime import datetime, timedelta, timezone

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

    def to_local_str(self, format_str: str = '%Y-%m-%d %H:%M:%S', tz = None) -> str:
        """Convert UTC datetime to specified timezone (or local timezone if None) and format as string.

        Args:
            format_str: Format string for strftime (default: '%Y-%m-%d %H:%M:%S')
            tz: Timezone to convert to (default: None, which uses the system's local timezone)

        Returns:
            Formatted string representation of the datetime in the specified timezone
        """
        # Convert to specified timezone or local timezone if None
        local_dt = self.v.astimezone(tz)
        # Format according to the specified format
        return local_dt.strftime(format_str)

    def __sub__(self, other: "UtcDatetime") -> timedelta:
        """Subtract another UtcDatetime from this one.

        Args:
            other: Another UtcDatetime object to subtract

        Returns:
            A timedelta object representing the time difference

        Raises:
            TypeError: If other is not a UtcDatetime object
        """
        if not isinstance(other, UtcDatetime):
            raise TypeError(f"unsupported operand type(s) for -: 'UtcDatetime' and '{type(other).__name__}'")

        return self.v - other.v
