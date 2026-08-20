from database.db import get_connection

def add_subscriber(email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO subscribers(email) VALUES (?)",
        (email,)
    )

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success

def remove_subscriber(email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM subscribers WHERE email = ?",
        (email,)
    )

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success

def get_subscribers():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM subscribers")

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]
