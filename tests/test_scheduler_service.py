from datetime import datetime, timedelta
from services.scheduler_service import format_offset, is_within_grace, REMINDER_GRACE_MINUTES

def test_format_offset_days():
    assert format_offset(1440) == "1 day(s)"
    assert format_offset(2880) == "2 day(s)"

def test_format_offset_hours():
    assert format_offset(60) == "1 hour(s)"
    assert format_offset(120) == "2 hour(s)"

def test_format_offset_minutes():
    assert format_offset(10) == "10 minute(s)"
    assert format_offset(45) == "45 minute(s)"

def test_is_within_grace_when_on_time():
    exec_time = datetime(2026, 8, 19, 12, 0, 0)
    now = exec_time

    assert is_within_grace(now, exec_time) is True

def test_is_within_grace_at_exact_boundary():
    exec_time = datetime(2026, 8, 19, 12, 0, 0)
    now = exec_time + timedelta(minutes=REMINDER_GRACE_MINUTES)

    assert is_within_grace(now, exec_time) is True

def test_is_within_grace_just_past_boundary():
    exec_time = datetime(2026, 8, 19, 12, 0, 0)
    now = exec_time + timedelta(minutes=REMINDER_GRACE_MINUTES, seconds=1)

    assert is_within_grace(now, exec_time) is False

def test_is_within_grace_stale_after_downtime():
    # Mirrors the real scenario: bot offline for hours, reminder now wildly overdue
    exec_time = datetime(2026, 8, 19, 1, 35, 0)
    now = exec_time + timedelta(hours=11)

    assert is_within_grace(now, exec_time) is False
