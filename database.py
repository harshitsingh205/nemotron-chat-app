import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classroom.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            reasoning TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def create_session(title="New Lesson"):
    session_id = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, title, now, now)
    )
    conn.commit()
    conn.close()
    return session_id

def list_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, updated_at FROM chat_sessions ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "updated_at": r["updated_at"]} for r in rows]

def get_session_messages(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, reasoning FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "reasoning": r["reasoning"]} for r in rows]

def add_message(session_id, role, content, reasoning=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages (session_id, role, content, reasoning) VALUES (?, ?, ?, ?)",
        (session_id, role, content, reasoning)
    )
    now = datetime.now().isoformat()
    cursor.execute(
        "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
        (now, session_id)
    )
    conn.commit()
    conn.close()

def update_session_title(session_id, new_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (new_title, session_id))
    conn.commit()
    conn.close()

def delete_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_database_stats():
    """Returns database size, session count, and message count for transparency."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM chat_sessions")
    session_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) AS count FROM chat_messages")
    message_count = cursor.fetchone()["count"]
    conn.close()

    file_size_kb = 0
    if os.path.exists(DB_PATH):
        file_size_kb = round(os.path.getsize(DB_PATH) / 1024, 2)

    return {
        "path": DB_PATH,
        "size_kb": file_size_kb,
        "sessions": session_count,
        "messages": message_count,
    }
