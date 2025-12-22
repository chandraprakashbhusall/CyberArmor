import sqlite3
from datetime import datetime
import os
import json

DB_NAME = "cyberarmor.db"
USERS_FILE = "users.json"

# ------------------- CONNECTION -------------------
def connect():
    return sqlite3.connect(DB_NAME)

# ------------------- INITIALIZATION -------------------
def init_db():
    conn = connect()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)

    # WIFI LOGS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ssid TEXT,
            signal INT,
            security TEXT,
            password TEXT,
            strength_level TEXT,
            entropy REAL,
            download REAL,
            upload REAL,
            ping REAL,
            timestamp TEXT
        )
    """)

    # PORT SCANS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS port_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            scan_type TEXT,
            open_ports TEXT,
            os_guess TEXT,
            timestamp TEXT
        )
    """)

    # LINK SCANS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            domain TEXT,
            risk_level INT DEFAULT 0,
            issues TEXT,
            timestamp TEXT
        )
    """)

    # FILE SCANS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            threat_count INT DEFAULT 0,
            risk_level INT DEFAULT 0,
            timestamp TEXT
        )
    """)

    # SYSTEM SCANS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_name TEXT,
            issues_count INT DEFAULT 0,
            threat_level INT DEFAULT 0,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()

    # Ensure JSON backup file exists
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)


# ------------------- USER FUNCTIONS -------------------
def add_user(username, email, password):
    """Register new user. Returns True if success, False if username/email exists"""
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (username, email, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

        # ✅ Backup to JSON
        backup_user_to_file(username, email, password)

        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def backup_user_to_file(username, email, password):
    """Save user to local JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    else:
        users = []

    users.append({
        "username": username,
        "email": email,
        "password": password,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def user_exists(username=None, email=None):
    conn = connect()
    cursor = conn.cursor()
    if username:
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    elif email:
        cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    else:
        conn.close()
        return False
    res = cursor.fetchone()
    conn.close()
    return bool(res)


def check_user(email, password):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE email=? AND password=?", (email, password))
    res = cursor.fetchone()
    conn.close()
    return res


# ------------------- SAVE FUNCTIONS -------------------
def save_wifi(ssid, signal, security, password, strength_level,
              entropy, download=None, upload=None, ping=None):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO wifi_logs 
        (ssid, signal, security, password, strength_level, entropy, download, upload, ping, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ssid, signal, security, password, strength_level, entropy,
        download, upload, ping, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def save_port_scan(target, scan_type, open_ports, os_guess):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO port_scans (target, scan_type, open_ports, os_guess, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        target, scan_type, str(open_ports), os_guess,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def save_link_scan(data):
    conn = connect()
    cursor = conn.cursor()
    issues = ", ".join(data.get("flags", []))
    cursor.execute("""
        INSERT INTO link_scans (url, domain, risk_level, issues, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("url", ""),
        data.get("domain", ""),
        int(data.get("risk_score", 0)),
        issues,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def save_file_scan(file_path, threat_count=0, risk_level=0):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO file_scans (file_path, threat_count, risk_level, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        file_path, threat_count, risk_level,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def save_system_scan(scan_name, issues_count=0, threat_level=0):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO system_scans (scan_name, issues_count, threat_level, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        scan_name, issues_count, threat_level,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


# ------------------- COUNT FUNCTIONS -------------------
def count_wifi_tests():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM wifi_logs")
    res = c.fetchone()[0]
    conn.close()
    return res


def count_port_scans():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM port_scans")
    res = c.fetchone()[0]
    conn.close()
    return res


def count_link_checks():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM link_scans")
    res = c.fetchone()[0]
    conn.close()
    return res


def count_file_scans():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM file_scans")
    res = c.fetchone()[0]
    conn.close()
    return res


def count_system_scans():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM system_scans")
    res = c.fetchone()[0]
    conn.close()
    return res


# ------------------- LAST THREAT LEVEL FUNCTIONS -------------------
def last_file_scan_threat_level():
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("SELECT risk_level FROM file_scans ORDER BY id DESC LIMIT 1")
        res = c.fetchone()
        return res[0] if res else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


def last_system_scan_threat_level():
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("SELECT threat_level FROM system_scans ORDER BY id DESC LIMIT 1")
        res = c.fetchone()
        return res[0] if res else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


# ------------------- RECENT ACTIVITY -------------------
def get_recent_activity(limit=10):
    conn = connect()
    c = conn.cursor()

    try:
        query = f"""
            SELECT 'WiFi', ssid || ' (' || signal || 'dBm)', timestamp
            FROM wifi_logs
            UNION ALL
            SELECT 'Port Scan', target || ' (' || scan_type || ')', timestamp
            FROM port_scans
            UNION ALL
            SELECT 'Link Scan', url || ' [risk ' || risk_level || ']', timestamp
            FROM link_scans
            UNION ALL
            SELECT 'File Scan', file_path || ' [risk ' || risk_level || ']', timestamp
            FROM file_scans
            UNION ALL
            SELECT 'System Scan', scan_name || ' [issues ' || threat_level || '%]', timestamp
            FROM system_scans
            ORDER BY timestamp DESC LIMIT {limit}
        """
        c.execute(query)
        rows = c.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows


# -----------------------------------------------------
# ⭐ ADDITIONS FOR LOGIN & REGISTER BELOW
# -----------------------------------------------------

def get_user_by_email(email):
    """Get user details by email"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, password FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_username(username):
    """Get user details by username"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, password FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def verify_credentials(email, password):
    """Return True if email+password match"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password))
    row = cur.fetchone()
    conn.close()
    return bool(row)


# ------------------- JSON FILE HELPERS -------------------
def get_user_file_data(email=None, username=None):
    """Get user from JSON file"""
    if not os.path.exists(USERS_FILE):
        return None

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    for u in users:
        if email and u["email"] == email:
            return u
        if username and u["username"] == username:
            return u
    return None
