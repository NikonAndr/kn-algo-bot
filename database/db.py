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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notified_events (
        repo TEXT,
        pr_number INTEGER,
        event_type TEXT,
        notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (repo, pr_number, event_type)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
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
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        offset_minutes INTEGER NOT NULL,
        exec_time TIMESTAMP NOT NULL,
        sent INTEGER DEFAULT 0,
        FOREIGN KEY (event_id) REFERENCES events(id)
    )
    """)

    conn.commit()
    conn.close()
