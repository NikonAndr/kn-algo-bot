from datetime import timedelta
from database.db import get_connection
from utils.time_helpers import warsaw_now

def create_event(google_event_id, title, description, start_time, end_time, event_type, source, created_by):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO events(google_event_id, title, description, start_time, end_time, event_type, source, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (google_event_id, title, description, start_time, end_time, event_type, source, created_by)
    )

    event_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return event_id

def get_event_by_google_id(google_event_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM events WHERE google_event_id = ?",
        (google_event_id,)
    )

    row = cursor.fetchone()

    conn.close()

    return row

def get_event(event_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM events WHERE id = ?",
        (event_id,)
    )

    row = cursor.fetchone()

    conn.close()

    return row

def update_event_details(event_id, title, description, start_time, end_time):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE events SET title = ?, description = ?, start_time = ?, end_time = ? WHERE id = ?",
        (title, description, start_time, end_time, event_id)
    )

    conn.commit()
    conn.close()

def mark_event_cancelled(event_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE events SET status = 'cancelled' WHERE id = ?",
        (event_id,)
    )

    conn.commit()
    conn.close()

def add_reminder(event_id, offset_minutes, exec_time):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO event_reminders(event_id, offset_minutes, exec_time) VALUES (?, ?, ?)",
        (event_id, offset_minutes, exec_time)
    )

    conn.commit()
    conn.close()

def reschedule_reminders(event_id, new_start_time):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, offset_minutes FROM event_reminders WHERE event_id = ? AND sent = 0",
        (event_id,)
    )

    rows = cursor.fetchall()

    for reminder_id, offset_minutes in rows:
        exec_time = new_start_time - timedelta(minutes=offset_minutes)

        cursor.execute(
            "UPDATE event_reminders SET exec_time = ? WHERE id = ?",
            (exec_time, reminder_id)
        )

    conn.commit()
    conn.close()

def cancel_reminders(event_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE event_reminders SET sent = 1 WHERE event_id = ? AND sent = 0",
        (event_id,)
    )

    conn.commit()
    conn.close()

def get_due_reminders():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT event_reminders.id, event_reminders.offset_minutes, events.title, events.start_time, event_reminders.exec_time
        FROM event_reminders
        JOIN events ON events.id = event_reminders.event_id
        WHERE event_reminders.sent = 0
          AND event_reminders.exec_time <= ?
          AND events.status = 'active'
        """,
        (warsaw_now(),)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows

def get_upcoming_events(limit=10):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM events
        WHERE status = 'active' AND start_time > ?
        ORDER BY start_time ASC
        LIMIT ?
        """,
        (warsaw_now(), limit)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows

def mark_reminder_sent(reminder_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE event_reminders SET sent = 1 WHERE id = ?",
        (reminder_id,)
    )

    conn.commit()
    conn.close()
