import sqlite3
from datetime import datetime
import os
import json
import hashlib

DB_NAME = "cyberarmor.db"
USERS_FILE = "users.json"


# =====================================================
# CONNECTION
# =====================================================

def connect():
    return sqlite3.connect(DB_NAME)


# =====================================================
# INIT
# =====================================================

def init_db():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        created_at TEXT NOT NULL

    )

    """)

    conn.commit()
    conn.close()

    if not os.path.exists(USERS_FILE):

        with open(USERS_FILE,"w") as f:

            json.dump([],f)


init_db()


# =====================================================
# HASH
# =====================================================

def hash_password(password):

    return hashlib.sha256(password.encode()).hexdigest()


def current_time():

    return datetime.now().isoformat()


# =====================================================
# REGISTER
# =====================================================

def add_user(username,email,password):

    if not username or not email or not password:

        return False


    conn=connect()
    cursor=conn.cursor()

    try:

        hashed=hash_password(password)

        created=current_time()

        cursor.execute("""

        INSERT INTO users(username,email,password,created_at)

        VALUES(?,?,?,?)

        """,(username,email,hashed,created))


        conn.commit()


        backup_user_to_file(
            username,
            email,
            hashed,
            created
        )

        return True


    except sqlite3.IntegrityError:

        return False


    finally:

        conn.close()


# =====================================================
# LOGIN
# =====================================================

def check_user(email,password):

    conn=connect()
    cursor=conn.cursor()

    hashed=hash_password(password)

    cursor.execute("""

    SELECT id,username,email,created_at

    FROM users

    WHERE email=? AND password=?

    """,(email,hashed))


    row=cursor.fetchone()

    conn.close()

    return row



def verify_credentials(email,password):

    return bool(check_user(email,password))



# =====================================================
# VERIFY PASSWORD
# =====================================================

def verify_password(user_id,password):

    conn=connect()

    cursor=conn.cursor()

    cursor.execute("""

    SELECT password FROM users

    WHERE id=?

    """,(user_id,))


    row=cursor.fetchone()

    conn.close()

    if not row:

        return False


    return row[0]==hash_password(password)



# =====================================================
# UPDATE PASSWORD
# =====================================================

def update_password(user_id,new_password):

    conn=connect()

    cursor=conn.cursor()

    cursor.execute("""

    UPDATE users

    SET password=?

    WHERE id=?

    """,(hash_password(new_password),user_id))


    conn.commit()

    conn.close()

    return True



# =====================================================
# USER LOOKUPS
# =====================================================

def user_exists(username=None,email=None):

    conn=connect()

    cursor=conn.cursor()


    if username:

        cursor.execute(
        "SELECT id FROM users WHERE username=?",
        (username,))

    elif email:

        cursor.execute(
        "SELECT id FROM users WHERE email=?",
        (email,))

    else:

        conn.close()

        return False


    row=cursor.fetchone()

    conn.close()

    return bool(row)



def get_user_by_email(email):

    conn=connect()

    cursor=conn.cursor()

    cursor.execute("""

    SELECT id,username,email,created_at

    FROM users

    WHERE email=?

    """,(email,))


    row=cursor.fetchone()

    conn.close()

    return row



def get_user_by_username(username):

    conn=connect()

    cursor=conn.cursor()

    cursor.execute("""

    SELECT id,username,email,created_at

    FROM users

    WHERE username=?

    """,(username,))


    row=cursor.fetchone()

    conn.close()

    return row



def get_user_by_id(user_id):

    conn=connect()

    cursor=conn.cursor()

    cursor.execute("""

    SELECT id,username,email,created_at

    FROM users

    WHERE id=?

    """,(user_id,))


    row=cursor.fetchone()

    conn.close()

    return row


# =====================================================
# DELETE
# =====================================================

def delete_user(email):

    conn=connect()

    cursor=conn.cursor()

    cursor.execute(
    "DELETE FROM users WHERE email=?",
    (email,))

    conn.commit()

    conn.close()


# =====================================================
# JSON BACKUP
# =====================================================

def backup_user_to_file(username,email,password,created):

    try:

        if os.path.exists(USERS_FILE):

            with open(USERS_FILE,"r") as f:

                users=json.load(f)

        else:

            users=[]

    except:

        users=[]


    users.append({

        "username":username,

        "email":email,

        "password":password,

        "created_at":created

    })


    with open(USERS_FILE,"w") as f:

        json.dump(users,f,indent=4)



# =====================================================
# JSON SEARCH
# =====================================================

def get_user_file_data(email=None,username=None):

    if not os.path.exists(USERS_FILE):

        return None


    try:

        with open(USERS_FILE,"r") as f:

            users=json.load(f)

    except:

        return None


    for u in users:

        if email and u["email"]==email:

            return u

        if username and u["username"]==username:

            return u


    return None


# ================= TOOL LOG TABLE =================

def init_logs():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        tool TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()
    conn.close()


init_logs()


def log_tool(username,tool):

    conn=connect()
    cur=conn.cursor()

    cur.execute(
    "INSERT INTO logs(username,tool) VALUES(?,?)",
    (username,tool))

    conn.commit()
    conn.close()



def tool_stats():

    conn=connect()
    cur=conn.cursor()

    cur.execute("""

    SELECT tool,COUNT(*)
    FROM logs
    GROUP BY tool

    """)

    rows=cur.fetchall()

    conn.close()

    data={}

    for r in rows:
        data[r[0]]=r[1]

    return data



def total_scans():

    conn=connect()
    cur=conn.cursor()

    cur.execute("SELECT COUNT(*) FROM logs")

    n=cur.fetchone()[0]

    conn.close()

    return n


# =====================================================
# ADMIN FUNCTIONS (NEW)
# =====================================================

def total_users():

    conn=connect()
    cur=conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")

    n=cur.fetchone()[0]

    conn.close()

    return n


def total_tools():

    stats=tool_stats()

    return len(stats)


def get_all_users():

    conn=connect()

    cur=conn.cursor()

    cur.execute("""

    SELECT username,email,created_at
    FROM users
    ORDER BY id DESC

    """)

    rows=cur.fetchall()

    conn.close()

    return rows


def search_users(keyword):

    conn=connect()

    cur=conn.cursor()

    cur.execute("""

    SELECT username,email,created_at
    FROM users
    WHERE username LIKE ? OR email LIKE ?

    """,(f"%{keyword}%",f"%{keyword}%"))


    rows=cur.fetchall()

    conn.close()

    return rows


def scans_per_user():

    conn=connect()

    cur=conn.cursor()

    cur.execute("""

    SELECT username,COUNT(*)
    FROM logs
    GROUP BY username

    """)

    rows=cur.fetchall()

    conn.close()

    return rows