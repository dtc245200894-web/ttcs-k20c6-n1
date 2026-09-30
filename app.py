from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request, session

from backend.database import Database
from backend.services import AuthService, RoomService


ROOT = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "hotel-management-local-development-key")
app.config["DATABASE_PATH"] = os.environ.get("DATABASE_PATH", os.path.join(ROOT, "hotel_management.db"))

database = Database(app.config["DATABASE_PATH"])
auth_service = AuthService(database)
room_service = RoomService(database)


@app.get("/")
def index():
    return render_template("index.html")


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


@app.get("/api/rooms")
def get_rooms():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    return jsonify({"ok": True, "rooms": room_service.list_rooms()})


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

    payload = request.get_json(silent=True) or {}
    ok, message, room = room_service.create_room(payload)
    return jsonify({"ok": ok, "message": message, "room": room}), 201 if ok else 400


@app.put("/api/rooms/<int:room_id>")
def update_room(room_id):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload = request.get_json(silent=True) or {}
    ok, message, room = room_service.update_room(room_id, payload)
    return jsonify({"ok": ok, "message": message, "room": room}), 200 if ok else 400


@app.delete("/api/rooms/<int:room_id>")
def delete_room(room_id):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    ok, message = room_service.delete_room(room_id)
    return jsonify({"ok": ok, "message": message}), 200 if ok else 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)