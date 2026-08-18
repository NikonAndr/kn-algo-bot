from database.db import get_connection
from utils.time_helpers import warsaw_now

def is_notified(repo, pr_number, event_type):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM notified_events WHERE repo = ? AND pr_number = ? AND event_type = ?",
        (repo, pr_number, event_type)
    )

    row = cursor.fetchone()

    conn.close()

    return row is not None

def mark_notified(repo, pr_number, event_type):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO notified_events(repo, pr_number, event_type, notified_at) VALUES (?, ?, ?, ?)",
        (repo, pr_number, event_type, warsaw_now())
    )

    conn.commit()
    conn.close()

def has_any_events(repo):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM notified_events WHERE repo = ? LIMIT 1",
        (repo,)
    )

    row = cursor.fetchone()

    conn.close()

    return row is not None
