"""Event location (Google Calendar's "where") and the google-calendar event type."""
import sqlite3
from datetime import datetime, timedelta

import database.db as db
from commands.events import format_events_list
from database import events as events_db
from services import calendar_service
from services.calendar_poll_service import CalendarPollService
from services.scheduler_service import format_reminder
from utils.time_helpers import warsaw_now

START = "2030-11-18T17:05:00+01:00"
END = "2030-11-18T18:30:00+01:00"


def calendar_item(google_id="g1", location=None, summary="Spotkanie KN ALGO"):
    item = {
        "id": google_id,
        "status": "confirmed",
        "summary": summary,
        "start": {"dateTime": START},
        "end": {"dateTime": END},
    }
    if location is not None:
        item["location"] = location
    return item


def sync(item):
    # sync_item doesn't touch the loop, so skip __init__ (which starts it).
    CalendarPollService.__new__(CalendarPollService).sync_item(item)


def location_of(row):
    return row[10]


# --- Schema migration (production DB predates the column) --------------------

OLD_EVENTS_SCHEMA = """
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_event_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    event_type TEXT DEFAULT 'other',
    source TEXT NOT NULL,
    created_by INTEGER,
    status TEXT DEFAULT 'active'
)
"""


def test_init_db_migrates_existing_events_table(tmp_path, monkeypatch):
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    conn.execute(OLD_EVENTS_SCHEMA)
    conn.execute("INSERT INTO events(google_event_id, title, start_time, event_type, source) VALUES ('a', 'From calendar', '2030-01-01 10:00:00', 'other', 'calendar')")
    conn.execute("INSERT INTO events(google_event_id, title, start_time, event_type, source) VALUES ('b', 'From bot', '2030-01-01 10:00:00', 'club_meeting', 'bot')")
    conn.execute("INSERT INTO events(google_event_id, title, start_time, event_type, source) VALUES ('c', 'Bot other', '2030-01-01 10:00:00', 'other', 'bot')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(db, "DB_PATH", str(db_path))

    db.init_db()
    db.init_db()  # runs on every bot start, so it must be idempotent

    rows = {row[1]: row for row in sqlite3.connect(db_path).execute("SELECT * FROM events")}
    assert rows["a"][6] == "google-calendar"
    assert rows["b"][6] == "club_meeting"
    assert rows["c"][6] == "other"
    assert location_of(rows["a"]) is None


# --- Calendar poller -----------------------------------------------------------

def test_calendar_event_stores_location_and_google_calendar_type(temp_db):
    sync(calendar_item(location="D1 sala 311a"))

    row = events_db.get_event_by_google_id("g1")
    assert location_of(row) == "D1 sala 311a"
    assert row[6] == "google-calendar"


def test_calendar_event_without_location(temp_db):
    sync(calendar_item())

    assert location_of(events_db.get_event_by_google_id("g1")) == ""


def test_location_added_later_in_google_is_synced(temp_db):
    sync(calendar_item())
    sync(calendar_item(location="D1 sala 311a"))

    assert location_of(events_db.get_event_by_google_id("g1")) == "D1 sala 311a"


# --- /create-event -> Google Calendar ------------------------------------------

class FakeInsert:
    def __init__(self, recorder, body):
        recorder.append(body)

    def execute(self):
        return {"id": "new-id"}


class FakeEventsResource:
    def __init__(self):
        self.bodies = []

    def insert(self, calendarId, body):
        return FakeInsert(self.bodies, body)


class FakeClient:
    def __init__(self):
        self.resource = FakeEventsResource()

    def events(self):
        return self.resource


def test_create_event_sends_location_to_google(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(calendar_service, "get_client", lambda: client)
    start = datetime(2030, 11, 18, 17, 5)

    calendar_service.create_event("Title", "", start, start + timedelta(hours=1), location="D1 sala 311a")

    assert client.resource.bodies[0]["location"] == "D1 sala 311a"


def test_bot_created_event_stores_location(temp_db):
    start = warsaw_now() + timedelta(hours=2)
    event_id = events_db.create_event(
        "g2", "Title", "", start, start, "other", "bot", None, location="D1 sala 311a"
    )

    assert location_of(events_db.get_event(event_id)) == "D1 sala 311a"


# --- /events list and reminders -------------------------------------------------

def test_events_list_shows_location(temp_db):
    sync(calendar_item(location="D1 sala 311a"))

    assert "D1 sala 311a" in format_events_list(events_db.get_upcoming_events())


def test_events_list_without_location_has_no_placeholder(temp_db):
    sync(calendar_item())

    text = format_events_list(events_db.get_upcoming_events())
    assert "📍" not in text and "None" not in text


def test_due_reminders_include_location(temp_db):
    sync(calendar_item(location="D1 sala 311a"))
    event_id = events_db.get_event_by_google_id("g1")[0]
    events_db.add_reminder(event_id, 60, warsaw_now() - timedelta(seconds=10))

    reminders = events_db.get_due_reminders()

    assert "D1 sala 311a" in reminders[-1]


def test_reminder_message_shows_location():
    message = format_reminder("Spotkanie KN ALGO", 60, "2030-11-18 17:05:00", "D1 sala 311a")

    assert "D1 sala 311a" in message and "Spotkanie KN ALGO" in message


def test_reminder_message_without_location():
    message = format_reminder("Spotkanie KN ALGO", 60, "2030-11-18 17:05:00", "")

    assert "📍" not in message and "None" not in message
