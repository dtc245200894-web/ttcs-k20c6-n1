from __future__ import annotations

import sqlite3
import re
from pathlib import Path

from werkzeug.security import generate_password_hash


DEMO_EMAIL = "admin@lotusstay.local"
DEMO_PASSWORD = "Hotel@123"
DEFAULT_ROOM_TYPES = (("single", "Single"), ("double", "Double"), ("vip", "VIP"))


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
            room_types_table_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'room_types'"
            ).fetchone() is not None
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'manager',
                    date_of_birth TEXT,
                    phone TEXT,
                    avatar_url TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            user_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(users)")
            }
            for column in ("date_of_birth", "phone", "avatar_url"):
                if column not in user_columns:
                    connection.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS room_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE
                )
                """
            )
            if not room_types_table_exists:
                connection.executemany(
                    "INSERT INTO room_types(slug, name) VALUES (?, ?)",
                    DEFAULT_ROOM_TYPES,
                )

            rooms_schema = """
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    image_url TEXT,
                    room_type TEXT NOT NULL REFERENCES room_types(slug),
                    price REAL NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available', 'occupied', 'cleaning', 'maintenance')),
                    floor INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            connection.execute(rooms_schema)
            for row in connection.execute("SELECT DISTINCT room_type FROM rooms"):
                room_type = str(row["room_type"])
                connection.execute(
                    "INSERT OR IGNORE INTO room_types(slug, name) VALUES (?, ?)",
                    (room_type, room_type.replace("-", " ").title()),
                )

            rooms_table = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'rooms'"
            ).fetchone()
            if rooms_table and re.search(r"CHECK\s*\(\s*room_type\s+IN", rooms_table["sql"], re.IGNORECASE):
                connection.execute("ALTER TABLE rooms RENAME TO rooms_legacy")
                connection.execute(rooms_schema)
                connection.execute(
                    """
                    INSERT INTO rooms(id, code, name, description, image_url, room_type, price, status, floor, created_at, updated_at)
                    SELECT id, code, name, description, image_url, room_type, price, status, floor, created_at, updated_at
                    FROM rooms_legacy
                    """
                )
                connection.execute("DROP TABLE rooms_legacy")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rentals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL REFERENCES rooms(id),
                    customer_name TEXT NOT NULL DEFAULT '',
                    customer_phone TEXT NOT NULL DEFAULT '',
                    starts_at TEXT NOT NULL,
                    ends_at TEXT NOT NULL,
                    nights INTEGER NOT NULL,
                    total_price REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed'))
                )
                """
            )
            rental_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(rentals)")
            }
            for column in ("customer_name", "customer_phone"):
                if column not in rental_columns:
                    connection.execute(
                        f"ALTER TABLE rentals ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
                    )
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS one_active_rental_per_room "
                "ON rentals(room_id) WHERE status = 'active'"
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

            connection.executemany(
                """
                INSERT OR IGNORE INTO rooms(code, name, description, image_url, room_type, price, status, floor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("A101", "Phòng Deluxe A101", "Phòng đôi rộng rãi với view xanh và giường ngủ êm ái.", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80", "double", 1800000, "available", 1),
                    ("A102", "Phòng Standard A102", "Phòng đơn thoải mái phù hợp cho khách công tác ngắn ngày.", "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=900&q=80", "single", 950000, "available", 1),
                    ("A103", "Phòng Superior A103", "Không gian nghỉ ngơi yên tĩnh, thiết kế hiện đại.", "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=900&q=80", "double", 1500000, "available", 1),
                    ("A104", "Phòng Standard A104", "Phòng đơn tiện nghi, phù hợp cho kỳ nghỉ ngắn ngày.", "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=900&q=80", "single", 900000, "available", 1),
                    ("A105", "Phòng Deluxe A105", "Phòng đôi thoáng sáng với nội thất cao cấp.", "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80", "double", 1900000, "available", 1),
                    ("A106", "Phòng Garden A106", "Phòng nghỉ hướng vườn với ban công riêng.", "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=900&q=80", "double", 2100000, "available", 1),
                    ("B201", "Phòng VIP B201", "Phòng VIP sang trọng với khu vực nghỉ ngơi riêng biệt.", "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=900&q=80", "vip", 3200000, "available", 2),
                    ("B202", "Phòng Family B202", "Phòng rộng cho gia đình, có 2 giường đơn và không gian làm việc.", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80", "double", 2400000, "available", 2),
                    ("B203", "Phòng Executive B203", "Phòng cao cấp có khu vực tiếp khách riêng.", "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=900&q=80", "vip", 3600000, "available", 2),
                    ("B204", "Phòng Family B204", "Phòng gia đình rộng rãi với hai giường lớn.", "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80", "double", 2600000, "available", 2),
                    ("B205", "Phòng Premium B205", "Phòng nghỉ cao cấp với tầm nhìn toàn cảnh thành phố.", "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=900&q=80", "vip", 3900000, "available", 2),
                    ("B206", "Phòng Twin B206", "Hai giường đơn riêng biệt, phù hợp cho bạn bè hoặc đồng nghiệp.", "https://images.unsplash.com/photo-1595576508898-0ad5c879a061?auto=format&fit=crop&w=900&q=80", "double", 2200000, "available", 2),
                    ("C301", "Phòng Family C301", "Phòng gia đình kết nối với khu vực sinh hoạt chung.", "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=80", "double", 2800000, "available", 3),
                    ("C302", "Phòng Honeymoon C302", "Không gian riêng tư dành cho kỳ nghỉ đặc biệt.", "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=900&q=80", "vip", 4200000, "available", 3),
                    ("C303", "Phòng Deluxe C303", "Phòng đôi rộng với khu vực làm việc tiện lợi.", "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=900&q=80", "double", 2300000, "available", 3),
                    ("C304", "Phòng Corner C304", "Phòng góc nhiều ánh sáng với cửa sổ lớn.", "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80", "double", 2500000, "available", 3),
                    ("D401", "Phòng Sky Suite D401", "Suite tầng cao với phòng khách và tầm nhìn rộng.", "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=900&q=80", "vip", 5200000, "available", 4),
                    ("D402", "Phòng Panorama D402", "Phòng cao cấp với cửa kính nhìn toàn cảnh.", "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=900&q=80", "vip", 4800000, "available", 4),
                    ("D403", "Phòng Family Suite D403", "Suite gia đình có phòng ngủ và khu vực sinh hoạt riêng.", "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80", "double", 4400000, "available", 4),
                ],
            )