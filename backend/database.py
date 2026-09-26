from __future__ import annotations

import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


DEMO_EMAIL = "admin@lotusstay.local"
DEMO_PASSWORD = "Hotel@123"


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'manager',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            existing_user = connection.execute(
                "SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)
            ).fetchone()
            if existing_user is None:
                connection.execute(
                    "INSERT INTO users(full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    (
                        "Quản lý khách sạn",
                        DEMO_EMAIL,
                        generate_password_hash(DEMO_PASSWORD),
                        "manager",
                    ),
                )