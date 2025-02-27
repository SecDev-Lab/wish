from datetime import datetime, timezone

from wish_models.utc_datetime import UtcDatetime


class TestUtcDatetime:
    def test_utc_timezone(self):
        # Test that the datetime is set to UTC if no timezone is provided
        dt = datetime(2025, 2, 16, 6, 28, 28)
        utc_dt = UtcDatetime(v=dt)
        assert utc_dt.v.tzinfo == timezone.utc

    def test_serialize(self):
        # Test that the datetime is serialized to ISO 8601 format
        dt = datetime(2025, 2, 16, 6, 28, 28, tzinfo=timezone.utc)
        utc_dt = UtcDatetime(v=dt)
        assert utc_dt.serialize() == "2025-02-16T06:28:28Z"

    def test_deserialize_from_string(self):
        # Test deserialization from an ISO 8601 string
        date_str = "2025-02-16T06:28:28Z"
        utc_dt = UtcDatetime.model_validate(date_str)
        assert utc_dt.v == datetime(2025, 2, 16, 6, 28, 28, tzinfo=timezone.utc)

    def test_now(self):
        # Test that the now method returns the current UTC datetime
        utc_dt = UtcDatetime.now()
        now = datetime.now(tz=timezone.utc)
        # Allow a small delta for the time difference
        assert (now - utc_dt.v).total_seconds() < 1
