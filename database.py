import sqlite3
import os
import uuid
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classroom.db")
BACKUP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classroom_backup.json")

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

    # If the database is completely empty (e.g., container just rebooted/slept),
    # check if an auto-backup JSON file exists on disk to auto-restore!
    auto_restore_from_file_if_empty()

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
    auto_backup_to_file()
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
    auto_backup_to_file()

def update_session_title(session_id, new_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (new_title, session_id))
    conn.commit()
    conn.close()
    auto_backup_to_file()

def delete_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    auto_backup_to_file()

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
        "backup_path": BACKUP_PATH,
        "size_kb": file_size_kb,
        "sessions": session_count,
        "messages": message_count,
    }

def export_all_data():
    """Exports all sessions and all their corresponding messages as a structured dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC")
    sessions = cursor.fetchall()

    result = []
    for s in sessions:
        cursor.execute(
            "SELECT role, content, reasoning, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
            (s["id"],)
        )
        msgs = cursor.fetchall()
        result.append({
            "id": s["id"],
            "title": s["title"],
            "created_at": s["created_at"],
            "updated_at": s["updated_at"],
            "messages": [{
                "role": m["role"],
                "content": m["content"],
                "reasoning": m["reasoning"],
                "created_at": m["created_at"]
            } for m in msgs]
        })
    conn.close()
    return {
        "version": 1,
        "exported_at": datetime.now().isoformat(),
        "total_sessions": len(result),
        "sessions": result
    }

def import_all_data(data):
    """
    Imports all sessions and messages from a dictionary or JSON string.
    Safely creates sessions and messages without duplicates.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return 0, 0

    sessions = []
    if isinstance(data, dict):
        sessions = data.get("sessions", [])
    elif isinstance(data, list):
        sessions = data

    if not sessions:
        return 0, 0

    conn = get_connection()
    cursor = conn.cursor()
    imported_sessions = 0
    imported_messages = 0

    for s in sessions:
        s_id = s.get("id") or str(uuid.uuid4())
        s_title = s.get("title", "Saved Lesson")
        created_at = s.get("created_at", datetime.now().isoformat())
        updated_at = s.get("updated_at", datetime.now().isoformat())

        cursor.execute(
            "INSERT OR REPLACE INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (s_id, s_title, created_at, updated_at)
        )
        imported_sessions += 1

        msgs = s.get("messages", [])
        for m in msgs:
            content = m.get("content", "")
            role = m.get("role", "user")
            cursor.execute(
                "SELECT id FROM chat_messages WHERE session_id = ? AND role = ? AND content = ?",
                (s_id, role, content)
            )
            existing = cursor.fetchone()
            if not existing:
                cursor.execute(
                    "INSERT INTO chat_messages (session_id, role, content, reasoning, created_at) VALUES (?, ?, ?, ?, ?)",
                    (s_id, role, content, m.get("reasoning"), m.get("created_at", datetime.now().isoformat()))
                )
                imported_messages += 1

    conn.commit()
    conn.close()
    auto_backup_to_file()
    return imported_sessions, imported_messages

def auto_backup_to_file():
    """Maintains an automated JSON backup on disk."""
    try:
        data = export_all_data()
        if data["total_sessions"] > 0:
            with open(BACKUP_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
    except Exception:
        pass

def auto_restore_from_file_if_empty():
    """If database has 0 sessions but backup file exists, automatically restore it."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS c FROM chat_sessions")
        count = cursor.fetchone()["c"]
        conn.close()

        if count == 0 and os.path.exists(BACKUP_PATH):
            with open(BACKUP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            import_all_data(data)
    except Exception:
        pass
