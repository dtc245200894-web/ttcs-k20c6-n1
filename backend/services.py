from __future__ import annotations

import re
import sqlite3
import unicodedata
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


class RoomService:
    ROOM_STATUSES = {"available", "occupied", "cleaning", "maintenance"}

    def __init__(self, database: Database) -> None:
        self.database = database

    def _normalize_room_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Dữ liệu phòng không hợp lệ.")

        code = str(payload.get("code", "")).strip().upper()
        name = str(payload.get("name", "")).strip()
        description = str(payload.get("description", "")).strip()
        image_url = str(payload.get("image_url", "")).strip()
        room_type = str(payload.get("room_type", "")).strip().lower()
        status = str(payload.get("status", "")).strip().lower()
        try:
            price = float(payload.get("price", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("Giá phòng không hợp lệ.") from exc
        try:
            floor = int(payload.get("floor", 1))
        except (TypeError, ValueError) as exc:
            raise ValueError("Tầng phòng không hợp lệ.") from exc

        if not code or len(code) > 20:
            raise ValueError("Mã phòng không hợp lệ.")
        if not name or len(name) > 120:
            raise ValueError("Tên phòng không hợp lệ.")
        if not image_url:
            raise ValueError("Vui lòng nhập đường dẫn hình ảnh phòng.")
        with self.database.connect() as connection:
            room_type_exists = connection.execute(
                "SELECT 1 FROM room_types WHERE slug = ?", (room_type,)
            ).fetchone()
        if room_type_exists is None:
            raise ValueError("Loại phòng không hợp lệ.")
        if status not in self.ROOM_STATUSES:
            raise ValueError("Trạng thái phòng không hợp lệ.")
        if price < 0:
            raise ValueError("Giá phòng phải lớn hơn hoặc bằng 0.")
        if floor < 1 or floor > 50:
            raise ValueError("Tầng phòng phải nằm trong khoảng 1-50.")

        return {
            "code": code,
            "name": name,
            "description": description or "Khách sạn Lotus Stay.",
            "image_url": image_url,
            "room_type": room_type,
            "price": round(price, 2),
            "status": status,
            "floor": floor,
        }

    def list_room_types(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT slug, name FROM room_types ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    def create_room_type(self, name: str) -> tuple[bool, str, dict[str, str] | None]:
        if not isinstance(name, str):
            return False, "Tên thể loại không hợp lệ.", None
        name = name.strip()
        if not name or len(name) > 40:
            return False, "Tên thể loại cần có từ 1 đến 40 ký tự.", None

        normalized_name = unicodedata.normalize("NFKD", name.lower().replace("đ", "d"))
        ascii_name = normalized_name.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
        if not slug:
            return False, "Tên thể loại cần chứa chữ cái hoặc chữ số không dấu.", None

        try:
            with self.database.connect() as connection:
                connection.execute(
                    "INSERT INTO room_types(slug, name) VALUES (?, ?)", (slug, name)
                )
        except sqlite3.IntegrityError:
            return False, "Thể loại phòng này đã tồn tại.", None
        return True, "Đã thêm thể loại phòng.", {"slug": slug, "name": name}

    def list_rooms(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM rooms ORDER BY floor, code ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def create_room(self, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        try:
            normalized = self._normalize_room_data(payload)
        except ValueError as exc:
            return False, str(exc), None

        try:
            with self.database.connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO rooms(code, name, description, image_url, room_type, price, status, floor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized["code"],
                        normalized["name"],
                        normalized["description"],
                        normalized["image_url"],
                        normalized["room_type"],
                        normalized["price"],
                        normalized["status"],
                        normalized["floor"],
                    ),
                )
                connection.commit()
                room = connection.execute(
                    "SELECT * FROM rooms WHERE id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
        except sqlite3.IntegrityError:
            return False, "Mã phòng đã tồn tại. Vui lòng chọn mã khác.", None

        return True, "Phòng mới đã được thêm.", dict(room)

    def update_room(self, room_id: int, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        try:
            normalized = self._normalize_room_data(payload)
        except ValueError as exc:
            return False, str(exc), None

        try:
            with self.database.connect() as connection:
                updated = connection.execute(
                    """
                    UPDATE rooms
                    SET code = ?, name = ?, description = ?, image_url = ?, room_type = ?, price = ?, status = ?, floor = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        normalized["code"],
                        normalized["name"],
                        normalized["description"],
                        normalized["image_url"],
                        normalized["room_type"],
                        normalized["price"],
                        normalized["status"],
                        normalized["floor"],
                        room_id,
                    ),
                )
                if updated.rowcount == 0:
                    return False, "Phòng không tồn tại.", None
                room = connection.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
        except sqlite3.IntegrityError:
            return False, "Mã phòng đã tồn tại. Vui lòng chọn mã khác.", None

        return True, "Thông tin phòng đã được cập nhật.", dict(room)

    def delete_room(self, room_id: int) -> tuple[bool, str]:
        with self.database.connect() as connection:
            deleted = connection.execute(
                "DELETE FROM rooms WHERE id = ? AND status = 'available'", (room_id,)
            )
            if deleted.rowcount == 0:
                room = connection.execute(
                    "SELECT id FROM rooms WHERE id = ?", (room_id,)
                ).fetchone()
                if room is None:
                    return False, "Phòng không tồn tại."
                return False, "Chỉ có thể xóa phòng đang trống."
        return True, "Phòng đã được xóa."