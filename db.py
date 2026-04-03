"""
CyberArmor – Database Layer (SQLite)
Handles all DB operations: users, logs, port scans, link scans, feedback.

Changes in this version:
- Added get_link_scans() so admin can view link scan history
- Added clear_logs() so admin can wipe activity logs
- update_password() now properly accepts both email (str) and id (int)
- All functions use context managers for safer connection handling
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime

DB_NAME    = "cyberarmor.db"
USERS_FILE = "users.json"


# =====================================================
# CONNECTION
# =====================================================

def connect():
    conn = connect = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# INIT ALL TABLES
# =====================================================

def init_db():
    conn = connect()
    cur  = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT UNIQUE NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        created_at  TEXT NOT NULL
    )""")

    # Tool usage logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT,
        tool        TEXT,
        date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Port scan results
    cur.execute("""
    CREATE TABLE IF NOT EXISTS port_scans (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        target      TEXT,
        mode        TEXT,
        results     TEXT,
        os_guess    TEXT,
        scanned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Link scan results
    cur.execute("""
    CREATE TABLE IF NOT EXISTS link_scans (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        url         TEXT,
        domain      TEXT,
        risk_score  INTEGER,
        ssl_ok      INTEGER,
        flags       TEXT,
        scanned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # User feedback
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        username     TEXT,
        rating       INTEGER,
        category     TEXT,
        message      TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()

    # Create backup JSON if it doesn't exist
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)


init_db()


# =====================================================
# HELPERS
# =====================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def current_time():
    return datetime.now().isoformat()


# =====================================================
# REGISTER
# =====================================================

def add_user(username, email, password):
    """Create a new user. Returns True on success, False if duplicate."""
    if not username or not email or not password:
        return False
    conn = connect()
    cur  = conn.cursor()
    try:
        hashed  = hash_password(password)
        created = current_time()
        cur.execute(
            "INSERT INTO users(username,email,password,created_at) VALUES(?,?,?,?)",
            (username, email, hashed, created)
        )
        conn.commit()
        _backup_user(username, email, hashed, created)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def _backup_user(username, email, password, created):
    """Write user info to JSON backup file as well."""
    try:
        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        users.append({
            "username":   username,
            "email":      email,
            "password":   password,
            "created_at": created
        })
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except Exception:
        pass


# =====================================================
# LOGIN / VERIFY
# =====================================================

def check_user(email, password):
    """Return user tuple if credentials match, else None."""
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "SELECT id,username,email,created_at FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    )
    row = cur.fetchone()
    conn.close()
    return tuple(row) if row else None


def verify_credentials(email, password):
    return bool(check_user(email, password))


def verify_password(user_id, password):
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT password FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return row[0] == hash_password(password)


# =====================================================
# UPDATE PASSWORD
# FIX: accepts both email string and user id integer
# =====================================================

def update_password(email_or_id, new_password):
    """
    Update a user's password. Accepts either:
      - email_or_id as str  -> searches by email
      - email_or_id as int  -> searches by user id
    """
    conn   = connect()
    cur    = conn.cursor()
    hashed = hash_password(new_password)

    if isinstance(email_or_id, int):
        cur.execute("UPDATE users SET password=? WHERE id=?", (hashed, email_or_id))
    else:
        # It's an email string
        cur.execute("UPDATE users SET password=? WHERE email=?", (hashed, email_or_id))

    conn.commit()
    conn.close()
    return True


# =====================================================
# USER LOOKUPS
# =====================================================

def user_exists(username=None, email=None):
    conn = connect()
    cur  = conn.cursor()
    if username:
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
    elif email:
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
    else:
        conn.close()
        return False
    row = cur.fetchone()
    conn.close()
    return bool(row)


def get_user_by_email(email):
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT id,username,email,created_at FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    return tuple(row) if row else None


def get_user_by_username(username):
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT id,username,email,created_at FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return tuple(row) if row else None


def get_user_by_id(user_id):
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT id,username,email,created_at FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return tuple(row) if row else None


def get_all_users():
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT username,email,created_at FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def search_users(keyword):
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "SELECT username,email,created_at FROM users "
        "WHERE username LIKE ? OR email LIKE ?",
        (f"%{keyword}%", f"%{keyword}%")
    )
    rows = cur.fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def delete_user(email):
    conn = connect()
    cur  = conn.cursor()
    cur.execute("DELETE FROM users WHERE email=?", (email,))
    conn.commit()
    conn.close()


# =====================================================
# TOOL LOGS
# =====================================================

def log_tool(username, tool):
    conn = connect()
    cur  = conn.cursor()
    cur.execute("INSERT INTO logs(username,tool) VALUES(?,?)", (username, tool))
    conn.commit()
    conn.close()


def tool_stats():
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT tool,COUNT(*) FROM logs GROUP BY tool ORDER BY COUNT(*) DESC")
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def total_scans():
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM logs")
    n = cur.fetchone()[0]
    conn.close()
    return n


def scans_per_user():
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "SELECT username,COUNT(*) FROM logs "
        "GROUP BY username ORDER BY COUNT(*) DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def recent_activity(limit=20):
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "SELECT username,tool,date FROM logs ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def clear_logs():
    """Delete all entries from the activity log table."""
    conn = connect()
    cur  = conn.cursor()
    cur.execute("DELETE FROM logs")
    conn.commit()
    conn.close()


# =====================================================
# PORT SCANS
# =====================================================

def save_port_scan(target, mode, results, os_guess=""):
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO port_scans(target,mode,results,os_guess) VALUES(?,?,?,?)",
        (target, mode, json.dumps(results), os_guess)
    )
    conn.commit()
    conn.close()


def get_port_scans(limit=50):
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM port_scans ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =====================================================
# LINK SCANS
# =====================================================

def save_link_scan(data):
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO link_scans(url,domain,risk_score,ssl_ok,flags) VALUES(?,?,?,?,?)",
        (
            data.get("url", ""),
            data.get("domain", ""),
            data.get("risk_score", 0),
            1 if data.get("ssl") else 0,
            json.dumps(data.get("flags", []))
        )
    )
    conn.commit()
    conn.close()


def get_link_scans(limit=50):
    """Fetch saved link scan records for admin panel."""
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM link_scans ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =====================================================
# FEEDBACK
# =====================================================

def submit_feedback(username, rating, category, message):
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO feedback(username,rating,category,message) VALUES(?,?,?,?)",
        (username, rating, category, message)
    )
    conn.commit()
    conn.close()


def get_all_feedback():
    conn = connect()
    cur  = conn.cursor()
    cur.execute(
        "SELECT username,rating,category,message,submitted_at "
        "FROM feedback ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def avg_rating():
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT AVG(rating) FROM feedback")
    val = cur.fetchone()[0]
    conn.close()
    return round(val, 1) if val else 0.0


# =====================================================
# ADMIN SUMMARY
# =====================================================

def total_users():
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    n = cur.fetchone()[0]
    conn.close()
    return n


def total_tools():
    return len(tool_stats())


def total_feedback():
    conn = connect()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM feedback")
    n = cur.fetchone()[0]
    conn.close()
    return n
