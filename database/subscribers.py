from database.db import get_connection

def add_subscriber(email, list_type="newsletter"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO subscribers(email, list_type) VALUES (?, ?)",
        (email, list_type)
    )

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success

def remove_subscriber(email, list_type="newsletter"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM subscribers WHERE email = ? AND list_type = ?",
        (email, list_type)
    )

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success

def get_subscribers(list_type="newsletter"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT email FROM subscribers WHERE list_type = ?",
        (list_type,)                   
    )

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]