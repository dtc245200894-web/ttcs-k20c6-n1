from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import date, datetime
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
                """
                SELECT id, full_name, email, password_hash, role, date_of_birth, phone, avatar_url
                FROM users WHERE email = ?
                """,
                (email.strip(),),
            ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            return None
        return {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "date_of_birth": user["date_of_birth"],
            "phone": user["phone"],
            "avatar_url": user["avatar_url"],
        }

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            user = connection.execute(
                """
                SELECT id, full_name, email, role, date_of_birth, phone, avatar_url
                FROM users WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        return dict(user) if user else None

    @staticmethod
    def validate_profile(
        full_name: str, date_of_birth: str, phone: str
    ) -> tuple[dict[str, str] | None, str]:
        if not all(isinstance(value, str) for value in (full_name, date_of_birth, phone)):
            return None, "Thông tin cá nhân không hợp lệ."

        full_name = full_name.strip()
        date_of_birth = date_of_birth.strip()
        phone = phone.strip()
        if not full_name or len(full_name) > 120:
            return None, "Vui lòng nhập họ tên hợp lệ."
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_of_birth):
            return None, "Vui lòng nhập ngày sinh hợp lệ."
        try:
            parsed_birth_date = date.fromisoformat(date_of_birth)
        except ValueError:
            return None, "Vui lòng nhập ngày sinh hợp lệ."
        if parsed_birth_date > date.today():
            return None, "Ngày sinh không được ở tương lai."
        if not re.fullmatch(r"[0-9]{10}", phone):
            return None, "Số điện thoại phải gồm đúng 10 chữ số."
        return {
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "phone": phone,
        }, ""

    def update_profile(
        self,
        user_id: int,
        full_name: str,
        date_of_birth: str,
        phone: str,
        avatar_url: str | None = None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        if not isinstance(avatar_url, str) or not avatar_url.strip():
            return False, "Vui lòng chọn ảnh đại diện.", None

        profile, message = self.validate_profile(full_name, date_of_birth, phone)
        if profile is None:
            return False, message, None

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE users
                SET full_name = ?, date_of_birth = ?, phone = ?, avatar_url = ?
                WHERE id = ?
                """,
                (
                    profile["full_name"],
                    profile["date_of_birth"],
                    profile["phone"],
                    avatar_url.strip(),
                    user_id,
                ),
            )
        user = self.get_profile(user_id)
        if user is None:
            return False, "Không tìm thấy tài khoản.", None
        return True, "Cập nhật thông tin cá nhân thành công.", user

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

    def delete_room_type(self, slug: str) -> tuple[bool, str]:
        if not isinstance(slug, str) or not slug.strip():
            return False, "Thể loại phòng không hợp lệ."
        slug = slug.strip()

        try:
            with self.database.connect() as connection:
                deleted = connection.execute(
                    """
                    DELETE FROM room_types
                    WHERE slug = ?
                      AND NOT EXISTS (
                          SELECT 1 FROM rooms WHERE rooms.room_type = room_types.slug
                      )
                    """,
                    (slug,),
                )
                if deleted.rowcount:
                    return True, "Đã xóa thể loại phòng."

                room_type = connection.execute(
                    "SELECT 1 FROM room_types WHERE slug = ?", (slug,)
                ).fetchone()
                if room_type is None:
                    return False, "Thể loại phòng không tồn tại."

                return False, "Không thể xóa thể loại phòng này."
        except sqlite3.IntegrityError:
            return False, "Không thể xóa thể loại phòng này."

    def move_rooms_to_room_type(
        self, source_slug: str, target_slug: str, room_ids: list[int]
    ) -> tuple[bool, str, int]:
        if not isinstance(source_slug, str) or not isinstance(target_slug, str):
            return False, "Thể loại phòng không hợp lệ.", 0
        source_slug = source_slug.strip()
        target_slug = target_slug.strip()
        if not source_slug or not target_slug:
            return False, "Vui lòng chọn thể loại nguồn và thể loại đích.", 0
        if source_slug == target_slug:
            return False, "Thể loại nguồn và đích phải khác nhau.", 0
        if not isinstance(room_ids, list) or not room_ids:
            return False, "Vui lòng chọn ít nhất một phòng cần chuyển.", 0
        if any(isinstance(room_id, bool) or not isinstance(room_id, int) or room_id < 1 for room_id in room_ids):
            return False, "Danh sách phòng cần chuyển không hợp lệ.", 0
        room_ids = list(dict.fromkeys(room_ids))

        with self.database.connect() as connection:
            room_types = connection.execute(
                "SELECT slug FROM room_types WHERE slug IN (?, ?)",
                (source_slug, target_slug),
            ).fetchall()
            if len(room_types) != 2:
                return False, "Thể loại nguồn hoặc đích không tồn tại.", 0

            placeholders = ", ".join("?" for _ in room_ids)
            matching_rooms = connection.execute(
                f"SELECT COUNT(*) FROM rooms WHERE room_type = ? AND id IN ({placeholders})",
                (source_slug, *room_ids),
            ).fetchone()[0]
            if matching_rooms != len(room_ids):
                return False, "Một số phòng đã chọn không còn thuộc thể loại hiện tại.", 0

            updated = connection.execute(
                f"UPDATE rooms SET room_type = ?, updated_at = CURRENT_TIMESTAMP WHERE room_type = ? AND id IN ({placeholders})",
                (target_slug, source_slug, *room_ids),
            )
            moved_count = updated.rowcount

        return True, f"Đã chuyển {moved_count} phòng đã chọn sang thể loại mới.", moved_count

    def list_rooms(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT rooms.*,
                       rentals.starts_at AS check_in,
                       rentals.ends_at AS check_out
                FROM rooms
                LEFT JOIN rentals ON rentals.room_id = rooms.id AND rentals.status = 'active'
                ORDER BY rooms.floor, rooms.code ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def rent_room(
        self, room_id: int, starts_at: str, ends_at: str
    ) -> tuple[bool, str, dict[str, Any] | None]:
        if isinstance(room_id, bool) or not isinstance(room_id, int) or room_id < 1:
            return False, "Phòng được chọn không hợp lệ.", None
        if not isinstance(starts_at, str) or not isinstance(ends_at, str):
            return False, "Vui lòng chọn thời gian trả phòng hợp lệ.", None
        try:
            start = datetime.fromisoformat(starts_at)
            checkout = datetime.fromisoformat(ends_at)
        except ValueError:
            return False, "Vui lòng chọn thời gian trả phòng hợp lệ.", None
        if start.tzinfo is not None or checkout.tzinfo is not None:
            return False, "Thời gian thuê phòng không hợp lệ.", None
        if abs((start - datetime.now()).total_seconds()) > 120:
            return False, "Giờ bắt đầu thuê đã thay đổi. Vui lòng thử lại.", None
        if checkout.time() != start.time():
            return False, "Giờ trả phòng phải trùng với giờ thuê phòng vào.", None
        nights = (checkout.date() - start.date()).days
        if nights < 1:
            return False, "Ngày trả phòng phải sau ngày thuê phòng.", None

        try:
            with self.database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                room = connection.execute(
                    "SELECT * FROM rooms WHERE id = ? AND status = 'available'",
                    (room_id,),
                ).fetchone()
                if room is None:
                    return False, "Phòng không tồn tại hoặc không còn trống.", None

                total_price = round(nights * room["price"], 2)
                start_value = start.isoformat(timespec="minutes")
                end_value = checkout.isoformat(timespec="minutes")
                connection.execute(
                    "INSERT INTO rentals(room_id, starts_at, ends_at, nights, total_price) VALUES (?, ?, ?, ?, ?)",
                    (room_id, start_value, end_value, nights, total_price),
                )
                updated = connection.execute(
                    "UPDATE rooms SET status = 'occupied', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'available'",
                    (room_id,),
                )
                if updated.rowcount == 0:
                    return False, "Phòng không còn trống. Vui lòng tải lại danh sách.", None
        except sqlite3.IntegrityError:
            return False, "Phòng đã có lượt thuê đang hoạt động.", None

        return True, "Thuê phòng thành công.", {
            "room_id": room_id,
            "check_in": start_value,
            "check_out": end_value,
            "nights": nights,
            "total_price": total_price,
        }

    def create_room(self, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        if isinstance(payload, dict):
            payload = {**payload, "status": "available"}
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
        if not isinstance(payload, dict):
            return False, "Dữ liệu phòng không hợp lệ.", None

        try:
            with self.database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                current_room = connection.execute(
                    "SELECT status FROM rooms WHERE id = ?", (room_id,)
                ).fetchone()
                if current_room is None:
                    return False, "Phòng không tồn tại.", None

                active_rental = connection.execute(
                    "SELECT 1 FROM rentals WHERE room_id = ? AND status = 'active'",
                    (room_id,),
                ).fetchone()
                requested_status = str(
                    payload.get("status", current_room["status"])
                ).strip().lower()
                if requested_status == "occupied" and current_room["status"] != "occupied":
                    return False, "Chỉ có thể chuyển phòng sang trạng thái đã thuê khi tạo lượt thuê.", None
                if requested_status == "occupied" and active_rental is None:
                    return False, "Chỉ phòng đang có người thuê mới được mang trạng thái đã thuê.", None
                if active_rental is not None and requested_status != "occupied":
                    return False, "Không thể đổi trạng thái phòng khi đang có người thuê.", None

                normalized = self._normalize_room_data(
                    {**payload, "status": requested_status}
                )
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
        except ValueError as exc:
            return False, str(exc), None
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