from __future__ import annotations

import re
import hashlib
import hmac
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta, timezone
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

    def issue_password_reset_code(self, email: str, code: str, secret: str) -> str:
        if not isinstance(email, str):
            return "ignored"
        email = email.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return "ignored"

        now = datetime.now(timezone.utc)
        with self.database.connect() as connection:
            user = connection.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if user is None:
                return "ignored"

            previous = connection.execute(
                "SELECT sent_at FROM password_reset_codes WHERE email = ?", (email,)
            ).fetchone()
            if previous is not None:
                sent_at = datetime.fromisoformat(previous["sent_at"])
                if now - sent_at < timedelta(seconds=60):
                    return "throttled"

            code_hash = hmac.new(
                secret.encode(), f"{email}:{code}".encode(), hashlib.sha256
            ).hexdigest()
            connection.execute(
                """
                INSERT INTO password_reset_codes(email, code_hash, expires_at, sent_at, attempts)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(email) DO UPDATE SET
                    code_hash = excluded.code_hash,
                    expires_at = excluded.expires_at,
                    sent_at = excluded.sent_at,
                    attempts = 0
                """,
                (
                    email,
                    code_hash,
                    (now + timedelta(minutes=10)).isoformat(),
                    now.isoformat(),
                ),
            )
        return "send"

    def clear_password_reset_code(self, email: str) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM password_reset_codes WHERE email = ?", (email,))

    def reset_password(
        self, email: str, code: str, new_password: str, secret: str
    ) -> tuple[bool, str]:
        if not all(isinstance(value, str) for value in (email, code, new_password)):
            return False, "Thông tin đặt lại mật khẩu không hợp lệ."

        email = email.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return False, "Email không hợp lệ."
        if not re.fullmatch(r"[0-9]{6}", code):
            return False, "Mã xác minh phải gồm 6 chữ số."
        if len(new_password) < 8 or len(new_password) > 128:
            return False, "Mật khẩu cần có từ 8 đến 128 ký tự."

        now = datetime.now(timezone.utc)
        with self.database.connect() as connection:
            reset = connection.execute(
                "SELECT * FROM password_reset_codes WHERE email = ?", (email,)
            ).fetchone()
            if reset is None:
                return False, "Mã xác minh không hợp lệ hoặc đã hết hạn."
            if datetime.fromisoformat(reset["expires_at"]) <= now:
                connection.execute(
                    "DELETE FROM password_reset_codes WHERE email = ?", (email,)
                )
                return False, "Mã xác minh không hợp lệ hoặc đã hết hạn."

            submitted_hash = hmac.new(
                secret.encode(), f"{email}:{code}".encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(reset["code_hash"], submitted_hash):
                if reset["attempts"] + 1 >= 5:
                    connection.execute(
                        "DELETE FROM password_reset_codes WHERE email = ?", (email,)
                    )
                else:
                    connection.execute(
                        "UPDATE password_reset_codes SET attempts = attempts + 1 WHERE email = ?",
                        (email,),
                    )
                return False, "Mã xác minh không hợp lệ hoặc đã hết hạn."

            connection.execute(
                "UPDATE users SET password_hash = ? WHERE email = ?",
                (generate_password_hash(new_password), email),
            )
            connection.execute(
                "DELETE FROM password_reset_codes WHERE email = ?", (email,)
            )
        return True, "Đổi mật khẩu thành công. Bạn có thể đăng nhập."

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> tuple[bool, str]:
        if not all(
            isinstance(value, str)
            for value in (current_password, new_password, confirm_password)
        ):
            return False, "Thông tin đổi mật khẩu không hợp lệ."
        if len(new_password) < 8 or len(new_password) > 128:
            return False, "Mật khẩu cần có từ 8 đến 128 ký tự."
        if new_password != confirm_password:
            return False, "Mật khẩu xác nhận không khớp."

        with self.database.connect() as connection:
            user = connection.execute(
                "SELECT password_hash FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if user is None:
                return False, "Không tìm thấy tài khoản."
            if not check_password_hash(user["password_hash"], current_password):
                return False, "Mật khẩu hiện tại không chính xác."

            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), user_id),
            )
        return True, "Đổi mật khẩu thành công."

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
        if not re.fullmatch(r"(?:09[0-9]{8}|034[0-9]{7})", phone):
            return None, "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 09 hoặc 034."
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

        now_value = datetime.now().replace(second=0, microsecond=0).isoformat(timespec="minutes")
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
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

            occupied_room = connection.execute(
                f"""
                SELECT 1 FROM rentals
                WHERE room_id IN ({placeholders}) AND status = 'active'
                  AND starts_at <= ? AND ends_at > ?
                LIMIT 1
                """,
                (*room_ids, now_value, now_value),
            ).fetchone()
            if occupied_room is not None:
                return False, "Không thể cập nhật thể loại khi phòng đang có người thuê.", 0

            updated = connection.execute(
                f"UPDATE rooms SET room_type = ?, updated_at = CURRENT_TIMESTAMP WHERE room_type = ? AND id IN ({placeholders})",
                (target_slug, source_slug, *room_ids),
            )
            moved_count = updated.rowcount

        return True, f"Đã chuyển {moved_count} phòng đã chọn sang thể loại mới.", moved_count

    def list_rooms(self) -> list[dict[str, Any]]:
        now = datetime.now().replace(second=0, microsecond=0)
        now_value = now.isoformat(timespec="minutes")
        with self.database.connect() as connection:
            room_rows = connection.execute(
                """
                SELECT *
                FROM rooms
                ORDER BY rooms.floor, rooms.code ASC
                """
            ).fetchall()
            rental_rows = connection.execute(
                """
                SELECT id, room_id, customer_name, customer_phone, customer_identity, starts_at, ends_at,
                       nights, total_price, status, cleaning_released
                FROM rentals
                ORDER BY starts_at, id
                """
            ).fetchall()

        rentals_by_room: dict[int, list[dict[str, Any]]] = {}
        for row in rental_rows:
            rentals_by_room.setdefault(row["room_id"], []).append(dict(row))

        rooms: list[dict[str, Any]] = []
        for row in room_rows:
            room = dict(row)
            room_rentals = rentals_by_room.get(room["id"], [])
            current_rental = next(
                (
                    rental
                    for rental in room_rentals
                    if rental["status"] == "active"
                    and rental["starts_at"] <= now_value < rental["ends_at"]
                ),
                None,
            )
            recent_checkout = next(
                (
                    rental
                    for rental in reversed(room_rentals)
                    if rental["status"] == "active"
                    and timedelta(0)
                    <= now - datetime.fromisoformat(rental["ends_at"])
                    < timedelta(minutes=30)
                ),
                None,
            )
            if room["status"] != "maintenance":
                if current_rental:
                    room["status"] = "occupied"
                elif recent_checkout and not recent_checkout["cleaning_released"]:
                    room["status"] = "cleaning"
                elif room["status"] != "cleaning":
                    room["status"] = "available"
            room["rentals"] = [
                rental for rental in room_rentals if rental["ends_at"] > now_value
            ]
            room["check_in"] = current_rental["starts_at"] if current_rental else None
            room["check_out"] = current_rental["ends_at"] if current_rental else None
            room["customer_name"] = current_rental["customer_name"] if current_rental else None
            room["customer_phone"] = current_rental["customer_phone"] if current_rental else None
            rooms.append(room)
        return rooms

    def list_rental_history(self) -> list[dict[str, Any]]:
        now_value = datetime.now().replace(second=0, microsecond=0).isoformat(timespec="minutes")
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT rentals.id, rentals.customer_name, rentals.customer_phone,
                       rentals.customer_identity, rentals.starts_at, rentals.ends_at,
                       rentals.nights, rentals.total_price, rooms.code AS room_code,
                       rooms.name AS room_name
                FROM rentals
                JOIN rooms ON rooms.id = rentals.room_id
                WHERE rentals.ends_at <= ?
                ORDER BY rentals.ends_at DESC, rentals.id DESC
                """,
                (now_value,),
            ).fetchall()
        return [dict(row) for row in rows]

    def checkout_rental(self, rental_id: int) -> tuple[bool, str, dict[str, Any] | None]:
        if isinstance(rental_id, bool) or not isinstance(rental_id, int) or rental_id < 1:
            return False, "Lượt thuê không hợp lệ.", None

        now_value = datetime.now().replace(second=0, microsecond=0).isoformat(timespec="minutes")
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rental = connection.execute(
                """
                SELECT id, room_id, starts_at, ends_at
                FROM rentals
                WHERE id = ? AND status = 'active'
                  AND starts_at <= ? AND ends_at > ?
                """,
                (rental_id, now_value, now_value),
            ).fetchone()
            if rental is None:
                return False, "Chỉ có thể trả phòng cho lượt thuê đang diễn ra.", None

            connection.execute(
                "UPDATE rentals SET ends_at = ? WHERE id = ?",
                (now_value, rental_id),
            )

        return True, "Đã trả phòng thành công.", {
            "id": rental["id"],
            "room_id": rental["room_id"],
            "check_out": now_value,
        }

    def delete_upcoming_rental(self, rental_id: int) -> tuple[bool, str]:
        if isinstance(rental_id, bool) or not isinstance(rental_id, int) or rental_id < 1:
            return False, "Lượt thuê không hợp lệ."

        now_value = datetime.now().replace(second=0, microsecond=0).isoformat(timespec="minutes")
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rental = connection.execute(
                """
                SELECT id FROM rentals
                WHERE id = ? AND status = 'active' AND starts_at > ?
                """,
                (rental_id, now_value),
            ).fetchone()
            if rental is None:
                return False, "Chỉ có thể xóa lịch thuê sắp tới."
            connection.execute("DELETE FROM rentals WHERE id = ?", (rental_id,))

        return True, "Đã xóa lịch đặt trước."

    def rent_room(
        self,
        room_id: int,
        starts_at: str,
        ends_at: str,
        customer_name: str,
        customer_phone: str,
        customer_identity: str,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        if isinstance(room_id, bool) or not isinstance(room_id, int) or room_id < 1:
            return False, "Phòng được chọn không hợp lệ.", None
        if not isinstance(customer_name, str) or not customer_name.strip() or len(customer_name.strip()) > 120:
            return False, "Vui lòng nhập tên khách hợp lệ.", None
        if not isinstance(customer_phone, str) or not re.fullmatch(r"(?:09\d{8}|034\d{7})", customer_phone.strip()):
            return False, "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 09 hoặc 034.", None
        if not isinstance(customer_identity, str) or not re.fullmatch(r"0\d{11}", customer_identity.strip()):
            return False, "Số CCCD phải gồm 12 chữ số và bắt đầu bằng 0.", None
        if not isinstance(starts_at, str) or not isinstance(ends_at, str):
            return False, "Vui lòng chọn thời gian trả phòng hợp lệ.", None
        try:
            start = datetime.fromisoformat(starts_at)
            checkout = datetime.fromisoformat(ends_at)
        except ValueError:
            return False, "Vui lòng chọn thời gian trả phòng hợp lệ.", None
        if start.tzinfo is not None or checkout.tzinfo is not None:
            return False, "Thời gian thuê phòng không hợp lệ.", None
        if start.date() < date.today():
            return False, "Ngày thuê phòng không được trước ngày hôm nay.", None
        if start < datetime.now().replace(second=0, microsecond=0):
            return False, "Giờ thuê phòng không được trước thời gian hiện tại.", None
        if checkout.time() != start.time():
            return False, "Giờ trả phòng phải trùng với giờ thuê phòng vào.", None
        nights = (checkout.date() - start.date()).days
        if nights < 1:
            return False, "Ngày trả phòng phải sau ngày thuê phòng.", None

        try:
            with self.database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                room = connection.execute(
                    "SELECT * FROM rooms WHERE id = ? AND status IN ('available', 'occupied')",
                    (room_id,),
                ).fetchone()
                if room is None:
                    return False, "Phòng không tồn tại hoặc hiện không thể cho thuê.", None

                total_price = round(nights * room["price"], 2)
                start_value = start.isoformat(timespec="minutes")
                end_value = checkout.isoformat(timespec="minutes")
                now_value = datetime.now().replace(second=0, microsecond=0).isoformat(
                    timespec="minutes"
                )
                minimum_gap = timedelta(minutes=30)
                overlapping_rental = connection.execute(
                    """
                    SELECT 1 FROM rentals
                    WHERE room_id = ? AND status = 'active'
                      AND (ends_at > ? OR cleaning_released = 0)
                      AND starts_at < ? AND ends_at > ?
                    LIMIT 1
                    """,
                    (
                        room_id,
                        now_value,
                        (checkout + minimum_gap).isoformat(timespec="minutes"),
                        (start - minimum_gap).isoformat(timespec="minutes"),
                    ),
                ).fetchone()
                if overlapping_rental is not None:
                    return False, "Các lượt thuê cùng phòng phải cách nhau ít nhất 30 phút.", None

                connection.execute(
                    "INSERT INTO rentals(room_id, customer_name, customer_phone, customer_identity, starts_at, ends_at, nights, total_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        room_id,
                        customer_name.strip(),
                        customer_phone.strip(),
                        customer_identity.strip(),
                        start_value,
                        end_value,
                        nights,
                        total_price,
                    ),
                )
        except sqlite3.IntegrityError:
            return False, "Không thể lưu lượt thuê do dữ liệu phòng đã thay đổi.", None

        return True, "Thuê phòng thành công.", {
            "room_id": room_id,
            "customer_name": customer_name.strip(),
            "customer_phone": customer_phone.strip(),
            "customer_identity": customer_identity.strip(),
            "check_in": start_value,
            "check_out": end_value,
            "nights": nights,
            "total_price": total_price,
        }

    def transfer_upcoming_rental(
        self,
        rental_id: int,
        target_room_id: int,
    ) -> tuple[bool, str]:
        if (
            isinstance(rental_id, bool)
            or not isinstance(rental_id, int)
            or rental_id < 1
            or isinstance(target_room_id, bool)
            or not isinstance(target_room_id, int)
            or target_room_id < 1
        ):
            return False, "Thông tin chuyển lịch không hợp lệ."

        try:
            with self.database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                now = datetime.now().replace(second=0, microsecond=0)
                now_value = now.isoformat(timespec="minutes")
                rental = connection.execute(
                    """
                    SELECT id, room_id, starts_at, ends_at
                    FROM rentals
                    WHERE id = ? AND status = 'active' AND starts_at > ?
                    """,
                    (rental_id, now_value),
                ).fetchone()
                if rental is None:
                    return False, "Chỉ có thể chuyển các lịch thuê sắp tới."
                if rental["room_id"] == target_room_id:
                    return False, "Vui lòng chọn phòng khác phòng hiện tại."

                target_room = connection.execute(
                    "SELECT status FROM rooms WHERE id = ?",
                    (target_room_id,),
                ).fetchone()
                if target_room is None or target_room["status"] in {
                    "cleaning",
                    "maintenance",
                }:
                    return False, "Phòng đích hiện không thể nhận lịch thuê."
                recent_checkout = connection.execute(
                    """
                    SELECT 1 FROM rentals
                    WHERE room_id = ? AND status = 'active'
                      AND cleaning_released = 0
                      AND ends_at > ? AND ends_at <= ?
                    LIMIT 1
                    """,
                    (
                        target_room_id,
                        (now - timedelta(minutes=30)).isoformat(timespec="minutes"),
                        now_value,
                    ),
                ).fetchone()
                if recent_checkout is not None:
                    return False, "Phòng đích hiện đang được dọn."

                minimum_gap = timedelta(minutes=30)
                conflicting_rental = connection.execute(
                    """
                    SELECT 1 FROM rentals
                    WHERE room_id = ? AND status = 'active'
                      AND starts_at < ? AND ends_at > ?
                    LIMIT 1
                    """,
                    (
                        target_room_id,
                        (
                            datetime.fromisoformat(rental["ends_at"]) + minimum_gap
                        ).isoformat(timespec="minutes"),
                        (
                            datetime.fromisoformat(rental["starts_at"]) - minimum_gap
                        ).isoformat(timespec="minutes"),
                    ),
                ).fetchone()
                if conflicting_rental is not None:
                    return False, "Thời gian trùng lặp."

                connection.execute(
                    "UPDATE rentals SET room_id = ? WHERE id = ?",
                    (target_room_id, rental_id),
                )
        except sqlite3.IntegrityError:
            return False, "Không thể chuyển lịch thuê do dữ liệu đã thay đổi."

        return True, "Đã chuyển lịch thuê sang phòng mới."

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

                now = datetime.now().replace(second=0, microsecond=0)
                now_value = now.isoformat(timespec="minutes")
                current_rental = connection.execute(
                    """
                    SELECT 1 FROM rentals
                    WHERE room_id = ? AND status = 'active'
                      AND starts_at <= ? AND ends_at > ?
                    LIMIT 1
                    """,
                    (room_id, now_value, now_value),
                ).fetchone()
                if current_rental is not None:
                    return False, "Không thể cập nhật phòng khi đang có người thuê.", None

                requested_status = str(
                    payload.get("status", current_room["status"])
                ).strip().lower()
                latest_checkout = connection.execute(
                    """
                    SELECT id, ends_at FROM rentals
                    WHERE room_id = ? AND status = 'active' AND ends_at <= ?
                    ORDER BY ends_at DESC, id DESC
                    LIMIT 1
                    """,
                    (room_id, now_value),
                ).fetchone()
                should_release_cleaning = (
                    requested_status == "available"
                    and current_rental is None
                    and latest_checkout is not None
                    and timedelta(0)
                    <= now - datetime.fromisoformat(latest_checkout["ends_at"])
                    < timedelta(minutes=30)
                )
                future_rental = connection.execute(
                    """
                    SELECT 1 FROM rentals
                    WHERE room_id = ? AND status = 'active' AND ends_at > ?
                    LIMIT 1
                    """,
                    (room_id, now_value),
                ).fetchone()
                if requested_status == "occupied" and current_rental is None:
                    return False, "Chỉ phòng đang có người thuê mới được mang trạng thái đã thuê.", None
                if future_rental is not None and requested_status in {"cleaning", "maintenance"}:
                    return False, "Không thể bảo trì hoặc dọn phòng khi đã có lịch thuê sắp tới.", None

                persisted_status = requested_status
                checkout_is_cleaning = (
                    latest_checkout is not None
                    and timedelta(0)
                    <= now - datetime.fromisoformat(latest_checkout["ends_at"])
                    < timedelta(minutes=30)
                )
                if (
                    requested_status == "cleaning"
                    and current_rental is None
                    and checkout_is_cleaning
                    and current_room["status"] != "cleaning"
                ):
                    persisted_status = current_room["status"]
                normalized = self._normalize_room_data(
                    {**payload, "status": persisted_status}
                )
                if should_release_cleaning and latest_checkout is not None:
                    connection.execute(
                        "UPDATE rentals SET cleaning_released = 1 WHERE id = ?",
                        (latest_checkout["id"],),
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