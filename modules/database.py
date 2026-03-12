"""
database.py
-----------
Módulo de gestión de base de datos para CyberShield AI.
Versión actualizada con historial de análisis, métricas reales y admin seguro.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import sqlite3
import hashlib
import datetime


# ─────────────────────────────────────────────
# CONEXIÓN Y CONFIGURACIÓN
# ─────────────────────────────────────────────

def get_connection(db_path: str = "users.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    c = conn.cursor()

    # Tabla usuarios con is_admin
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    """)
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Tabla reportes
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter   TEXT    NOT NULL,
            aggressor  TEXT    NOT NULL,
            message    TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        )
    """)

    # Tabla historial de análisis
    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL,
            type       TEXT    NOT NULL,
            input_text TEXT    NOT NULL,
            score      INTEGER NOT NULL,
            level      TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        )
    """)

    conn.commit()
    _ensure_default_admin(conn)


def _ensure_default_admin(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE is_admin = 1")
    if c.fetchone() is None:
        try:
            c.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)",
                ("admin", hash_password("Luchybean2026"))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            c.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
            conn.commit()


# ─────────────────────────────────────────────
# SEGURIDAD
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────────

def create_user(conn, username: str, password: str) -> bool:
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (?, ?, 0)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(conn, username: str, password: str) -> bool:
    c = conn.cursor()
    c.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )
    return c.fetchone() is not None


def is_admin(conn, username: str) -> bool:
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    return bool(row and row[0] == 1)


def promote_to_admin(conn, username: str) -> bool:
    c = conn.cursor()
    c.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
    conn.commit()
    return c.rowcount > 0


def get_all_users(conn):
    import pandas as pd
    return pd.read_sql_query("SELECT id, username, is_admin FROM users", conn)


def count_users(conn) -> int:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]


# ─────────────────────────────────────────────
# REPORTES
# ─────────────────────────────────────────────

def save_report(conn, reporter: str, aggressor: str, message: str) -> None:
    c = conn.cursor()
    c.execute(
        "INSERT INTO reports (reporter, aggressor, message, created_at) VALUES (?, ?, ?, ?)",
        (reporter, aggressor, message, datetime.datetime.now().isoformat())
    )
    conn.commit()


def get_all_reports(conn):
    import pandas as pd
    return pd.read_sql_query("SELECT * FROM reports ORDER BY created_at DESC", conn)


def count_reports(conn) -> int:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM reports")
    return c.fetchone()[0]


def get_reports_by_day(conn):
    """Retorna conteo de reportes agrupados por día (últimos 30 días)."""
    import pandas as pd
    return pd.read_sql_query("""
        SELECT DATE(created_at) as fecha, COUNT(*) as total
        FROM reports
        WHERE created_at >= DATE('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY fecha ASC
    """, conn)


# ─────────────────────────────────────────────
# HISTORIAL DE ANÁLISIS
# ─────────────────────────────────────────────

def save_analysis(conn, username: str, type: str, input_text: str, score: int, level: str) -> None:
    """
    Guarda un análisis de toxicidad en el historial.

    Args:
        username   : Usuario que hizo el análisis.
        type       : Tipo de análisis ('texto', 'instagram', 'lote').
        input_text : Texto o username analizado.
        score      : Puntuación de toxicidad 0-100.
        level      : Nivel ('safe', 'warning', 'danger').
    """
    c = conn.cursor()
    c.execute(
        "INSERT INTO analysis_history (username, type, input_text, score, level, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (username, type, input_text[:200], score, level, datetime.datetime.now().isoformat())
    )
    conn.commit()


def get_user_history(conn, username: str):
    import pandas as pd
    return pd.read_sql_query("""
        SELECT type, input_text, score, level, created_at
        FROM analysis_history
        WHERE username = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, conn, params=(username,))


def get_all_history(conn):
    import pandas as pd
    return pd.read_sql_query("""
        SELECT username, type, input_text, score, level, created_at
        FROM analysis_history
        ORDER BY created_at DESC
        LIMIT 200
    """, conn)


def count_analyses(conn) -> int:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM analysis_history")
    return c.fetchone()[0]


def count_toxic_analyses(conn) -> int:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM analysis_history WHERE level = 'danger'")
    return c.fetchone()[0]
