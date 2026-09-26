from __future__ import annotations

from typing import Any

from werkzeug.security import check_password_hash

from backend.database import Database


class AuthService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def login(self, email: str, password: str) -> dict[str, Any] | None:
        if not isinstance(email, str) or not isinstance(password, str):
            return None
        with self.database.connect() as connection:
            user = connection.execute(
                "SELECT id, full_name, email, password_hash, role FROM users WHERE email = ?",
                (email.strip(),),
            ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            return None
        return {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        }