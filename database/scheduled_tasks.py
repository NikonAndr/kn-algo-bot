import json
from database.db import get_connection

def add_task(task_type, payload, exec_time):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO scheduled_tasks(task_type, payload, exec_time) VALUES (?, ?, ?)",
        (task_type, json.dumps(payload, ensure_ascii=False), exec_time)
    )

    conn.commit()
    conn.close()

def get_due_tasks():
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, task_type, payload
    FROM scheduled_tasks
    WHERE executed = 0 AND exec_time <= datetime('now')
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows 

def mark_task_done(task_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE scheduled_tasks SET executed = 1 WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()