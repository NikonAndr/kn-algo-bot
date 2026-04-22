from database.db import get_connection

def create_note(title, content, author_id, author_name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO weekly_notes(title, content, author_id, author_name) VALUES (?, ?, ?, ?)",
        (title, content, author_id, author_name)
    )

    conn.commit()
    conn.close()

def get_notes_by_author(author_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM weekly_notes WHERE author_id = ? AND status != 'sent' ORDER BY created_at DESC",
        (author_id, )
    )

    notes = cursor.fetchall()

    conn.close()
    return notes

def get_note(note_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM weekly_notes WHERE id = ?",
        (note_id, )
    )

    note = cursor.fetchone()

    conn.close()
    return note

def update_note(note_id, title, content):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE weekly_notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, content, note_id)
    )

    conn.commit()
    conn.close()

def set_status(note_id, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE weekly_notes SET status = ? WHERE id = ?",
        (status, note_id)
    )

    conn.commit()
    conn.close()

def get_approved_notes():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM weekly_notes WHERE status = 'approved'"
    )

    notes = cursor.fetchall()
    conn.close()

    return notes

def get_draft_notes():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM weekly_notes WHERE status = 'draft'"
    )

    notes = cursor.fetchall()
    conn.close()   

    return notes