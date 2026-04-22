import sqlite3

DB_PATH = "data/database.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        email TEXT,
        list_type TEXT,
        PRIMARY KEY (email, list_type)
    )               
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_type TEXT,
        payload TEXT,
        exec_time TIMESTAMP,
        executed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP               
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weekly_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        author_name TEXT NOT NULL,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )               
    """)

    conn.commit()
    conn.close()
