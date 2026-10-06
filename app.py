from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from backend.database import Database
from backend.services import AuthService, RoomService


ROOT = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "hotel-management-local-development-key")
app.config["DATABASE_PATH"] = os.environ.get("DATABASE_PATH", os.path.join(ROOT, "hotel_management.db"))
app.config["UPLOAD_FOLDER"] = os.path.join(ROOT, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

database = Database(app.config["DATABASE_PATH"])
auth_service = AuthService(database)
room_service = RoomService(database)


def _room_payload_from_request():
    if request.mimetype == "multipart/form-data":
        payload = request.form.to_dict()
    else:
        payload = request.get_json(silent=True) or {}

    uploaded_image = request.files.get("image")
    if uploaded_image is None or not uploaded_image.filename:
        return payload, None, None

    extension = Path(secure_filename(uploaded_image.filename)).suffix.lower()
    header = uploaded_image.stream.read(12)
    uploaded_image.stream.seek(0)
    valid_image = (
        extension in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff")
    ) or (
        extension == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n")
    ) or (
        extension == ".webp" and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    )
    if not valid_image:
        return None, None, "Tệp không hợp lệ. Vui lòng chọn ảnh JPG, PNG hoặc WebP."

    filename = f"{uuid4().hex}{extension}"
    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    saved_path = upload_folder / filename
    uploaded_image.save(saved_path)
    payload["image_url"] = url_for("static", filename=f"uploads/{filename}")
    return payload, saved_path, None


def _remove_upload(path):
    if path is not None:
        path.unlink(missing_ok=True)


@app.get("/")
def index():
    return render_template("index.html", today=date.today().isoformat())


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")
    user = auth_service.login(email, password)
    if not user:
        return jsonify({"ok": False, "message": "Email hoặc mật khẩu không chính xác."}), 401

    session.clear()
    session["user"] = user
    return jsonify({"ok": True, "message": "Đăng nhập thành công.", "user": user})


@app.post("/api/register")
def register():
    payload = request.get_json(silent=True) or {}
    ok, message = auth_service.register(
        payload.get("full_name", ""),
        payload.get("email", ""),
        payload.get("password", ""),
    )
    return jsonify({"ok": ok, "message": message}), 201 if ok else 400


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "Bạn đã đăng xuất."})


@app.get("/api/session")
def current_session():
    return jsonify({"user": session.get("user")})


@app.get("/api/profile")
def get_profile():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    profile = auth_service.get_profile(user["id"])
    if profile is None:
        session.clear()
        return jsonify({"ok": False, "message": "Không tìm thấy tài khoản."}), 404
    return jsonify({"ok": True, "user": profile})


@app.put("/api/profile")
def update_profile():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    if request.mimetype != "multipart/form-data":
        return jsonify({"ok": False, "message": "Dữ liệu cập nhật không hợp lệ."}), 400

    avatar = request.files.get("avatar")
    if avatar is None or not avatar.filename:
        return jsonify({"ok": False, "message": "Vui lòng chọn ảnh đại diện."}), 400

    avatar_url = None
    saved_path = None
    extension = Path(secure_filename(avatar.filename)).suffix.lower()
    header = avatar.stream.read(12)
    avatar.stream.seek(0)
    valid_image = (
        extension in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff")
    ) or (
        extension == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n")
    ) or (
        extension == ".webp" and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    )
    if not valid_image:
        return jsonify({
            "ok": False,
            "message": "Ảnh đại diện không hợp lệ. Chọn ảnh JPG, PNG hoặc WebP.",
        }), 400

    payload = request.form
    profile, message = auth_service.validate_profile(
        payload.get("full_name", ""),
        payload.get("date_of_birth", ""),
        payload.get("phone", ""),
    )
    if profile is None:
        return jsonify({"ok": False, "message": message}), 400

    filename = f"{uuid4().hex}{extension}"
    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    saved_path = upload_folder / filename
    avatar.save(saved_path)
    avatar_url = url_for("static", filename=f"uploads/{filename}")

    valid, message, updated_user = auth_service.update_profile(
        user["id"],
        profile["full_name"],
        profile["date_of_birth"],
        profile["phone"],
        avatar_url=avatar_url,
    )
    if not valid:
        _remove_upload(saved_path)
        return jsonify({"ok": False, "message": message}), 400

    if updated_user is None:
        if saved_path is not None:
            _remove_upload(saved_path)
        return jsonify({"ok": False, "message": "Không thể tải thông tin tài khoản."}), 500
    session["user"] = updated_user
    return jsonify({"ok": True, "message": "Cập nhật thông tin cá nhân thành công.", "user": updated_user})


@app.get("/api/rooms")
def get_rooms():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    return jsonify({"ok": True, "rooms": room_service.list_rooms()})


@app.post("/api/rentals")
def create_rental():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload = request.get_json(silent=True) or {}
    room_id = payload.get("room_id")
    if isinstance(room_id, str) and room_id.isdigit():
        room_id = int(room_id)
    if isinstance(room_id, bool) or not isinstance(room_id, int):
        return jsonify({"ok": False, "message": "Phòng được chọn không hợp lệ."}), 400
    customer_identity = payload.get("customer_identity")
    if not isinstance(customer_identity, str):
        return jsonify({"ok": False, "message": "Số CCCD khách phải gồm đúng 12 chữ số."}), 400
    ok, message, rental = room_service.rent_room(
        room_id,
        payload.get("starts_at"),
        payload.get("ends_at"),
        payload.get("customer_name"),
        payload.get("customer_phone"),
        customer_identity,
    )
    return jsonify({"ok": ok, "message": message, "rental": rental}), 201 if ok else 400


@app.put("/api/rentals/<int:rental_id>/transfer")
def transfer_upcoming_rental(rental_id):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload = request.get_json(silent=True) or {}
    target_room_id = payload.get("target_room_id")
    if isinstance(target_room_id, str) and target_room_id.isdigit():
        target_room_id = int(target_room_id)
    if isinstance(target_room_id, bool) or not isinstance(target_room_id, int):
        return jsonify({"ok": False, "message": "Phòng đích không hợp lệ."}), 400

    ok, message = room_service.transfer_upcoming_rental(rental_id, target_room_id)
    return jsonify({"ok": ok, "message": message}), 200 if ok else 400


@app.get("/api/room-types")
def get_room_types():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    return jsonify({"ok": True, "room_types": room_service.list_room_types()})


@app.post("/api/room-types")
def create_room_type():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload = request.get_json(silent=True) or {}
    ok, message, room_type = room_service.create_room_type(payload.get("name", ""))
    return jsonify({"ok": ok, "message": message, "room_type": room_type}), 201 if ok else 400


@app.delete("/api/room-types/<string:slug>")
def delete_room_type(slug):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    ok, message = room_service.delete_room_type(slug)
    return jsonify({"ok": ok, "message": message}), 200 if ok else 400


@app.put("/api/room-types/move-rooms")
def move_rooms_to_room_type():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload = request.get_json(silent=True) or {}
    ok, message, moved_count = room_service.move_rooms_to_room_type(
        payload.get("source_slug", ""),
        payload.get("target_slug", ""),
        payload.get("room_ids", []),
    )
    return jsonify({"ok": ok, "message": message, "moved_count": moved_count}), 200 if ok else 400


@app.post("/api/rooms")
def create_room():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload, uploaded_image, error = _room_payload_from_request()
    if error:
        return jsonify({"ok": False, "message": error}), 400
    ok, message, room = room_service.create_room(payload)
    if not ok:
        _remove_upload(uploaded_image)
    return jsonify({"ok": ok, "message": message, "room": room}), 201 if ok else 400


@app.put("/api/rooms/<int:room_id>")
def update_room(room_id):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload, uploaded_image, error = _room_payload_from_request()
    if error:
        return jsonify({"ok": False, "message": error}), 400
    ok, message, room = room_service.update_room(room_id, payload)
    if not ok:
        _remove_upload(uploaded_image)
    return jsonify({"ok": ok, "message": message, "room": room}), 200 if ok else 400


@app.errorhandler(413)
def upload_too_large(_error):
    return jsonify({"ok": False, "message": "Dung lượng ảnh tối đa là 5 MB."}), 413


@app.delete("/api/rooms/<int:room_id>")
def delete_room(room_id):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    ok, message = room_service.delete_room(room_id)
    return jsonify({"ok": ok, "message": message}), 200 if ok else 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)