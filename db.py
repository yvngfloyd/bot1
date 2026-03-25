import sqlite3
from contextlib import closing

DB_PATH = "bot.db"


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            service TEXT,
            slot TEXT,
            client_name TEXT,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS callback_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            client_name TEXT,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            question TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()


def save_booking(
    user_id: int,
    username: str,
    service: str,
    slot: str,
    client_name: str,
    phone: str,
) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO bookings (user_id, username, service, slot, client_name, phone)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, service, slot, client_name, phone))
        conn.commit()


def save_callback(
    user_id: int,
    username: str,
    client_name: str,
    phone: str,
) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO callback_requests (user_id, username, client_name, phone)
        VALUES (?, ?, ?, ?)
        """, (user_id, username, client_name, phone))
        conn.commit()


def save_question(
    user_id: int,
    username: str,
    question: str,
) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO questions (user_id, username, question)
        VALUES (?, ?, ?)
        """, (user_id, username, question))
        conn.commit()
