import json
from database.db import get_connection
from utils.time_helpers import warsaw_now

def add_task(task_type, payload, exec_time):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO scheduled_tasks(task_type, payload, exec_time, created_at) VALUES (?, ?, ?, ?)",
        (task_type, json.dumps(payload, ensure_ascii=False), exec_time, warsaw_now())
    )

    conn.commit()
    conn.close()

def get_due_tasks():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, task_type, payload
        FROM scheduled_tasks
        WHERE executed = 0 AND exec_time <= ?
        """,
        (warsaw_now(),)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows

def has_pending_task(task_type):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM scheduled_tasks WHERE task_type = ? AND executed = 0 LIMIT 1",
        (task_type,)
    )

    row = cursor.fetchone()

    conn.close()

    return row is not None

def mark_task_done(task_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE scheduled_tasks SET executed = 1 WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()