"""
database.py
-----------
Database management module for CyberShield AI.
Handles SQLite connection, table creation, and user CRUD operations.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import sqlite3
import hashlib


# ─────────────────────────────────────────────
# CONNECTION AND CONFIGURATION
# ─────────────────────────────────────────────

def get_connection(db_path: str = "users.db") -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.

    Args:
        db_path (str): Path to the database file.

    Returns:
        sqlite3.Connection: Active database connection.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """
    Initializes the required tables in the database if they don't exist.

    Tables created:
        - users: stores user credentials (username, password hash).
        - reports: stores incidents reported by users.
        - analysis_history: stores analysis history per user.

    Args:
        conn (sqlite3.Connection): Active database connection.
    """
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter   TEXT    NOT NULL,
            aggressor  TEXT    NOT NULL,
            message    TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL,
            type       TEXT    NOT NULL,
            input_text TEXT,
            score      INTEGER,
            level      TEXT,
            created_at TEXT    NOT NULL
        )
    """)

    # Create default admin user if it doesn't exist
    try:
        c.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)",
            ("admin", hashlib.sha256("Luchybean2026".encode()).hexdigest())
        )
    except sqlite3.IntegrityError:
        pass  # Admin already exists

    conn.commit()


# ─────────────────────────────────────────────
# SECURITY: PASSWORD HASHING
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Generates a SHA-256 hash of the provided password.

    Args:
        password (str): Plain text password.

    Returns:
        str: SHA-256 hexadecimal hash.

    Note:
        SHA-256 without salt is acceptable for this educational version,
        but in production it is recommended to use bcrypt or argon2.
    """
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────────

def create_user(conn: sqlite3.Connection, username: str, password: str) -> bool:
    """
    Registers a new user in the database.

    Args:
        conn     (sqlite3.Connection): Active connection.
        username (str): Desired username.
        password (str): Plain text password (stored as hash).

    Returns:
        bool: True if user was created, False if username already exists.
    """
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(conn: sqlite3.Connection, username: str, password: str) -> bool:
    """
    Verifies a user's credentials.

    Args:
        conn     (sqlite3.Connection): Active connection.
        username (str): Username.
        password (str): Plain text password.

    Returns:
        bool: True if credentials are correct, False otherwise.
    """
    c = conn.cursor()
    c.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )
    return c.fetchone() is not None


def is_admin(conn: sqlite3.Connection, username: str) -> bool:
    """
    Checks if a user has admin privileges.

    Args:
        conn     (sqlite3.Connection): Active connection.
        username (str): Username to check.

    Returns:
        bool: True if user is admin, False otherwise.
    """
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    return bool(row and row[0])


def get_all_users(conn: sqlite3.Connection):
    """
    Returns all registered users.

    Args:
        conn (sqlite3.Connection): Active connection.

    Returns:
        pd.DataFrame: DataFrame with columns id, username.
    """
    import pandas as pd
    return pd.read_sql_query("SELECT id, username FROM users", conn)


# ─────────────────────────────────────────────
# REPORT OPERATIONS
# ─────────────────────────────────────────────

def save_report(conn: sqlite3.Connection, reporter: str, aggressor: str, message: str) -> None:
    """
    Saves a reported incident to the database.

    Args:
        conn      (sqlite3.Connection): Active connection.
        reporter  (str): Username of the reporting user.
        aggressor (str): Username or identifier of the aggressor.
        message   (str): Incident description.
    """
    import datetime
    c = conn.cursor()
    c.execute(
        "INSERT INTO reports (reporter, aggressor, message, created_at) VALUES (?, ?, ?, ?)",
        (reporter, aggressor, message, datetime.datetime.now().isoformat())
    )
    conn.commit()


def get_all_reports(conn: sqlite3.Connection):
    """
    Returns all stored reports.

    Args:
        conn (sqlite3.Connection): Active connection.

    Returns:
        pd.DataFrame: DataFrame with columns id, reporter, aggressor, message, created_at.
    """
    import pandas as pd
    return pd.read_sql_query("SELECT * FROM reports ORDER BY created_at DESC", conn)


# ─────────────────────────────────────────────
# ANALYSIS HISTORY OPERATIONS
# ─────────────────────────────────────────────

def save_analysis(conn, username, analysis_type, input_text, score, level):
    """Saves an analysis to the history table."""
    import datetime
    c = conn.cursor()
    c.execute(
        "INSERT INTO analysis_history (username, type, input_text, score, level, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (username, analysis_type, input_text, score, level, datetime.datetime.now().isoformat())
    )
    conn.commit()


def get_user_history(conn, username):
    """Returns the analysis history for a specific user."""
    import pandas as pd
    return pd.read_sql_query(
        "SELECT type, input_text, score, level, created_at FROM analysis_history WHERE username = ? ORDER BY created_at DESC",
        conn, params=(username,)
    )


def get_all_history(conn):
    """Returns the complete analysis history (admin only)."""
    import pandas as pd
    return pd.read_sql_query(
        "SELECT * FROM analysis_history ORDER BY created_at DESC", conn
    )


def count_users(conn) -> int:
    """Returns the total number of registered users."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]


def count_reports(conn) -> int:
    """Returns the total number of reported incidents."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM reports")
    return c.fetchone()[0]


def count_analyses(conn) -> int:
    """Returns the total number of analyses performed."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM analysis_history")
    return c.fetchone()[0]


def count_toxic_analyses(conn) -> int:
    """Returns the number of analyses with danger level."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM analysis_history WHERE level = 'danger'")
    return c.fetchone()[0]


def get_reports_by_day(conn):
    """Returns a DataFrame with report counts grouped by day (last 30 days)."""
    import pandas as pd
    return pd.read_sql_query(
        "SELECT DATE(created_at) as fecha, COUNT(*) as total FROM reports WHERE created_at >= DATE('now', '-30 days') GROUP BY DATE(created_at) ORDER BY fecha",
        conn
    )
