"""
db.py — SQLite database for FractalAuth
Stores all user data including fractal markers, behavior profiles, puzzles.
"""

import sqlite3
import json
import os
import hashlib
import threading

DB_PATH = os.environ.get("FRACTALAUTH_DB", "fractalauth.db")
_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock:
        conn = get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username        TEXT PRIMARY KEY,
                email           TEXT NOT NULL,
                password_hash   TEXT NOT NULL,
                registered_ip   TEXT DEFAULT '',
                registered_ua   TEXT DEFAULT '',
                registered_at   REAL DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                fractal_type    TEXT DEFAULT 'mandelbrot',
                fractal_markers TEXT DEFAULT '[]',
                behavior_profile TEXT DEFAULT '{}',
                easy_puzzle     TEXT DEFAULT '{}',
                hard_puzzle     TEXT DEFAULT '{}',
                is_complete     INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def user_exists(username: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row is not None


def create_user(username: str, email: str, password: str, ip: str = "", ua: str = ""):
    import time
    with _lock:
        conn = get_conn()
        conn.execute(
            "INSERT INTO users (username,email,password_hash,registered_ip,registered_ua,registered_at) VALUES (?,?,?,?,?,?)",
            (username, email, hash_password(password), ip, ua, time.time())
        )
        conn.commit()
        conn.close()


def get_user(username: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    # Deserialize JSON fields
    for field in ("fractal_markers", "behavior_profile", "easy_puzzle", "hard_puzzle"):
        try:
            d[field] = json.loads(d[field])
        except Exception:
            d[field] = [] if field == "fractal_markers" else {}
    return d


def update_field(username: str, field: str, value):
    """Update a single field. JSON-encodes dicts/lists."""
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    with _lock:
        conn = get_conn()
        conn.execute(f"UPDATE users SET {field}=? WHERE username=?", (value, username))
        conn.commit()
        conn.close()


def update_many(username: str, fields: dict):
    """Update multiple fields at once."""
    if not fields:
        return
    sets = []
    vals = []
    for k, v in fields.items():
        sets.append(f"{k}=?")
        vals.append(json.dumps(v) if isinstance(v, (dict, list)) else v)
    vals.append(username)
    with _lock:
        conn = get_conn()
        conn.execute(f"UPDATE users SET {','.join(sets)} WHERE username=?", vals)
        conn.commit()
        conn.close()


def increment_failed(username: str):
    with _lock:
        conn = get_conn()
        conn.execute(
            "UPDATE users SET failed_attempts=failed_attempts+1 WHERE username=?",
            (username,)
        )
        conn.commit()
        conn.close()


def reset_failed(username: str):
    with _lock:
        conn = get_conn()
        conn.execute("UPDATE users SET failed_attempts=0 WHERE username=?", (username,))
        conn.commit()
        conn.close()


def delete_user(username: str):
    with _lock:
        conn = get_conn()
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        conn.close()


# Auto-initialise on import
init_db()
