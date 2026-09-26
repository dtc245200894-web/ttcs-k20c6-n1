from __future__ import annotations

import re
import sqlite3
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

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

    def register(self, full_name: str, email: str, password: str) -> tuple[bool, str]:
        if not all(isinstance(value, str) for value in (full_name, email, password)):
            return False, "Thông tin đăng ký không hợp lệ."

        full_name = full_name.strip()
        email = email.strip().lower()
        if not full_name or len(full_name) > 120:
            return False, "Vui lòng nhập họ tên hợp lệ."
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return False, "Vui lòng nhập email hợp lệ."
        if len(password) < 8 or len(password) > 128:
            return False, "Mật khẩu cần có từ 8 đến 128 ký tự."

        try:
            with self.database.connect() as connection:
                connection.execute(
                    "INSERT INTO users(full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    (full_name, email, generate_password_hash(password), "staff"),
                )
        except sqlite3.IntegrityError:
            return False, "Email này đã được đăng ký."
        return True, "Tạo tài khoản thành công. Bạn có thể đăng nhập ngay."