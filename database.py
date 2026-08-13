import sqlite3
import os

DATABASE = "coding_tracker.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    print("DATABASE USED:",os.path.abspath(DATABASE))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS coding_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration INTEGER
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")