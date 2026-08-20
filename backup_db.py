import os
import sqlite3
from datetime import datetime

from database.db import DB_PATH

BACKUP_DIR = "data/backups"

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    dest_path = os.path.join(BACKUP_DIR, f"database-{datetime.now():%Y-%m-%d}.db")

    src_conn = sqlite3.connect(DB_PATH)
    dest_conn = sqlite3.connect(dest_path)

    with dest_conn:
        src_conn.backup(dest_conn)

    src_conn.close()
    dest_conn.close()

    print(f"Backed up {DB_PATH} to {dest_path}")

if __name__ == "__main__":
    backup()
