from datetime import timedelta
from utils.time_helpers import warsaw_now
from database import events as events_db

def make_event(google_event_id="g1", event_type="other", source="bot"):
    start = warsaw_now() + timedelta(hours=2)
    end = start + timedelta(hours=1)

    event_id = events_db.create_event(
        google_event_id, "Test Event", "desc", start, end, event_type, source, None
    )

    return event_id, start, end

def test_create_and_get_event(temp_db):
    event_id, start, end = make_event()

    row = events_db.get_event(event_id)

    assert row is not None
    assert row[2] == "Test Event"
    assert row[9] == "active"

def test_get_event_by_google_id(temp_db):
    event_id, _, _ = make_event(google_event_id="abc123")

    row = events_db.get_event_by_google_id("abc123")

    assert row is not None
    assert row[0] == event_id

def test_update_event_details(temp_db):
    event_id, start, end = make_event()
    new_start = start + timedelta(hours=1)
    new_end = end + timedelta(hours=1)

    events_db.update_event_details(event_id, "New Title", "new desc", new_start, new_end)

    row = events_db.get_event(event_id)
    assert row[2] == "New Title"
    assert row[3] == "new desc"
    assert row[4] == str(new_start)

def test_mark_event_cancelled(temp_db):
    event_id, _, _ = make_event()

    events_db.mark_event_cancelled(event_id)

    row = events_db.get_event(event_id)
    assert row[9] == "cancelled"

def test_reminder_only_due_once_exec_time_passes(temp_db):
    event_id, start, _ = make_event()

    future_exec_time = warsaw_now() + timedelta(hours=1)
    events_db.add_reminder(event_id, 60, future_exec_time)

    assert events_db.get_due_reminders() == []

    past_exec_time = warsaw_now() - timedelta(minutes=1)
    events_db.add_reminder(event_id, 10, past_exec_time)

    due = events_db.get_due_reminders()
    assert len(due) == 1
    assert due[0][1] == 10  # offset_minutes

def test_mark_reminder_sent_excludes_from_due(temp_db):
    event_id, _, _ = make_event()
    past_exec_time = warsaw_now() - timedelta(minutes=1)
    events_db.add_reminder(event_id, 10, past_exec_time)

    due = events_db.get_due_reminders()
    reminder_id = due[0][0]

    events_db.mark_reminder_sent(reminder_id)

    assert events_db.get_due_reminders() == []

def test_cancel_reminders_suppresses_without_deleting(temp_db):
    event_id, _, _ = make_event()
    past_exec_time = warsaw_now() - timedelta(minutes=1)
    events_db.add_reminder(event_id, 10, past_exec_time)

    events_db.cancel_reminders(event_id)

    assert events_db.get_due_reminders() == []

def test_reschedule_reminders_recomputes_exec_time(temp_db):
    event_id, start, _ = make_event()
    events_db.add_reminder(event_id, 60, start - timedelta(minutes=60))

    new_start = start + timedelta(days=1)
    events_db.reschedule_reminders(event_id, new_start)

    # After rescheduling to a day later, the reminder shouldn't be due yet
    assert events_db.get_due_reminders() == []

def test_due_reminders_excludes_cancelled_events(temp_db):
    event_id, _, _ = make_event()
    past_exec_time = warsaw_now() - timedelta(minutes=1)
    events_db.add_reminder(event_id, 10, past_exec_time)

    events_db.mark_event_cancelled(event_id)

    assert events_db.get_due_reminders() == []

def make_event_at(hours_offset, google_event_id):
    start = warsaw_now() + timedelta(hours=hours_offset)
    end = start + timedelta(hours=1)

    return events_db.create_event(
        google_event_id, f"Event {google_event_id}", "desc", start, end, "other", "bot", None
    )

def test_upcoming_events_ordered_soonest_first(temp_db):
    make_event_at(5, "later")
    make_event_at(1, "sooner")
    make_event_at(3, "middle")

    upcoming = events_db.get_upcoming_events()

    titles = [row[2] for row in upcoming]
    assert titles == ["Event sooner", "Event middle", "Event later"]

def test_upcoming_events_respects_limit(temp_db):
    for i in range(5):
        make_event_at(i + 1, f"event{i}")

    upcoming = events_db.get_upcoming_events(limit=3)

    assert len(upcoming) == 3

def test_upcoming_events_excludes_cancelled(temp_db):
    event_id = make_event_at(1, "cancel-me")
    events_db.mark_event_cancelled(event_id)

    assert events_db.get_upcoming_events() == []

def test_upcoming_events_excludes_past(temp_db):
    make_event_at(-1, "already-started")

    assert events_db.get_upcoming_events() == []
