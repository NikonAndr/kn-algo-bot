from datetime import datetime, timezone
from utils.time_helpers import parse_naive_timestamp, to_warsaw_naive

def test_parse_naive_timestamp_with_microseconds():
    parsed = parse_naive_timestamp("2026-08-19 14:00:00.123456")
    assert parsed == datetime(2026, 8, 19, 14, 0, 0, 123456)

def test_parse_naive_timestamp_without_microseconds():
    parsed = parse_naive_timestamp("2026-08-19 14:00:00")
    assert parsed == datetime(2026, 8, 19, 14, 0, 0)

def test_to_warsaw_naive_converts_utc_to_local_summer_offset():
    # August is CEST (UTC+2) in Warsaw
    utc_dt = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
    result = to_warsaw_naive(utc_dt)

    assert result == datetime(2026, 8, 19, 14, 0, 0)
    assert result.tzinfo is None
