from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request, session

from backend.database import Database
from backend.services import AuthService


ROOT = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "hotel-management-local-development-key")
app.config["DATABASE_PATH"] = os.environ.get("DATABASE_PATH", os.path.join(ROOT, "hotel_management.db"))

database = Database(app.config["DATABASE_PATH"])
auth_service = AuthService(database)


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


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "Bạn đã đăng xuất."})


@app.get("/api/session")
def current_session():
    return jsonify({"user": session.get("user")})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)