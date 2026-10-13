from __future__ import annotations

import os
import secrets
import smtplib
import ssl
from calendar import monthrange
from datetime import date, datetime
from email.message import EmailMessage
from io import BytesIO
from math import ceil, floor, log10
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, send_file, session, url_for
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename

from backend.database import Database
from backend.services import AuthService, RoomService


ROOT = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "hotel-management-local-development-key")
app.config["DATABASE_PATH"] = os.environ.get("DATABASE_PATH", os.path.join(ROOT, "hotel_management.db"))
app.config["UPLOAD_FOLDER"] = os.path.join(ROOT, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["SMTP_HOST"] = os.environ.get("SMTP_HOST", "")
app.config["SMTP_PORT"] = os.environ.get("SMTP_PORT", "587")
app.config["SMTP_USERNAME"] = os.environ.get("SMTP_USERNAME", "")
app.config["SMTP_PASSWORD"] = os.environ.get("SMTP_PASSWORD", "")
app.config["SMTP_FROM"] = os.environ.get("SMTP_FROM", "")
app.config["SMTP_USE_TLS"] = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

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


def _send_password_reset_email(email, code):
    if not app.config["SMTP_HOST"] or not app.config["SMTP_FROM"]:
        return False

    message = EmailMessage()
    message["Subject"] = "Mã xác minh đặt lại mật khẩu Lotus Stay"
    message["From"] = app.config["SMTP_FROM"]
    message["To"] = email
    message.set_content(
        f"Mã xác minh đặt lại mật khẩu của bạn là: {code}\n"
        "Mã có hiệu lực trong 10 phút. Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )
    try:
        with smtplib.SMTP(
            app.config["SMTP_HOST"], int(app.config["SMTP_PORT"]), timeout=10
        ) as server:
            if app.config["SMTP_USE_TLS"]:
                server.starttls(context=ssl.create_default_context())
            if app.config["SMTP_USERNAME"]:
                server.login(app.config["SMTP_USERNAME"], app.config["SMTP_PASSWORD"])
            server.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        app.logger.exception("Could not send password reset email")
        return False
    return True


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


@app.post("/api/password-reset/request")
def request_password_reset():
    if not app.config["SMTP_HOST"] or not app.config["SMTP_FROM"]:
        return jsonify({
            "ok": False,
            "message": "Máy chủ email chưa được cấu hình. Vui lòng liên hệ quản trị viên.",
        }), 503

    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    code = f"{secrets.randbelow(1_000_000):06d}"
    result = auth_service.issue_password_reset_code(email, code, app.config["SECRET_KEY"])
    if result == "send" and not _send_password_reset_email(email.strip().lower(), code):
        auth_service.clear_password_reset_code(email.strip().lower())
        return jsonify({"ok": False, "message": "Không thể gửi email lúc này. Vui lòng thử lại sau."}), 503
    return jsonify({
        "ok": True,
        "message": "Nếu email đã đăng ký, mã xác minh sẽ được gửi tới hộp thư của bạn.",
    })


@app.post("/api/password-reset/complete")
def complete_password_reset():
    payload = request.get_json(silent=True) or {}
    ok, message = auth_service.reset_password(
        payload.get("email", ""),
        payload.get("code", ""),
        payload.get("new_password", ""),
        app.config["SECRET_KEY"],
    )
    return jsonify({"ok": ok, "message": message}), 200 if ok else 400


@app.post("/api/password/change")
def change_password():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    ok, message = auth_service.change_password(
        user["id"],
        payload.get("current_password", ""),
        payload.get("new_password", ""),
        payload.get("confirm_password", ""),
    )
    return jsonify({"ok": ok, "message": message}), 200 if ok else 400


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


@app.get("/api/rentals/history")
def get_rental_history():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    return jsonify({"ok": True, "rentals": room_service.list_rental_history()})


@app.post("/api/rentals/revenue/export")
def export_revenue_pdf():
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "message": "Thông tin thống kê không hợp lệ."}), 400

    year = payload.get("year")
    month = payload.get("month")
    if (
        isinstance(year, bool)
        or not isinstance(year, int)
        or year < 1
        or year > 9999
        or (month is not None and (
            isinstance(month, bool)
            or not isinstance(month, int)
            or month < 1
            or month > 12
        ))
    ):
        return jsonify({"ok": False, "message": "Năm hoặc tháng thống kê không hợp lệ."}), 400

    font_candidates = (
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    )
    font_path = next((path for path in font_candidates if path.is_file()), None)
    if font_path is None:
        app.logger.error("No Unicode TrueType font is available for revenue PDF export")
        return jsonify({
            "ok": False,
            "message": "Máy chủ chưa có font Unicode để tạo PDF. Vui lòng liên hệ quản trị viên.",
        }), 500

    font_name = "RevenueUnicode"
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

    period_count = monthrange(year, month)[1] if month is not None else 12
    period_totals = [0] * period_count
    monthly_daily_totals = {}
    for rental in room_service.list_rental_history():
        checkout_date = str(rental.get("ends_at") or "")[:10]
        try:
            completed_on = datetime.strptime(checkout_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if completed_on.year == year:
            amount = int(rental.get("total_price") or 0)
            daily_totals = monthly_daily_totals.setdefault(completed_on.month, {})
            daily_totals[completed_on.day] = daily_totals.get(completed_on.day, 0) + amount
            if month is None or completed_on.month == month:
                period_index = completed_on.month - 1 if month is None else completed_on.day - 1
                period_totals[period_index] += amount

    period_title = (
        f"Thu nhập tháng {month:02d} năm {year}"
        if month is not None
        else f"Thu nhập năm {year}"
    )
    total_income = sum(period_totals)
    rows = [["Kỳ thống kê", "Thu nhập"]]
    for index, amount in enumerate(period_totals, start=1):
        label = (
            f"Ngày {index:02d}/{month:02d}/{year}"
            if month is not None
            else f"Tháng {index:02d}/{year}"
        )
        rows.append([label, f"{amount:,}".replace(",", ".") + " đ"])

    chart_width = A4[0] - 96
    chart_height = 180
    chart = Drawing(chart_width, chart_height)
    plot_left, plot_right = 48, chart_width - 8
    plot_bottom, plot_top = 30, chart_height - 14
    plot_width = plot_right - plot_left
    plot_height = plot_top - plot_bottom
    max_period_total = max(period_totals, default=0)
    raw_scale_step = max_period_total / 4 if max_period_total else 250_000
    scale_magnitude = 10 ** floor(log10(raw_scale_step))
    normalized_scale_step = raw_scale_step / scale_magnitude
    scale_step = (
        1 if normalized_scale_step <= 1
        else 2 if normalized_scale_step <= 2
        else 5 if normalized_scale_step <= 5
        else 10
    ) * scale_magnitude
    scale_maximum = max(
        4 * scale_step,
        ceil(max_period_total / scale_step) * scale_step,
    )
    tick_count = round(scale_maximum / scale_step)
    chart_color = colors.HexColor("#426b59")
    grid_color = colors.HexColor("#dfe5df")

    def format_axis_amount(amount: float) -> str:
        if amount >= 1_000_000:
            value = amount / 1_000_000
            suffix = " tr"
        elif amount >= 1_000:
            value = amount / 1_000
            suffix = " k"
        else:
            value = amount
            suffix = ""
        formatted = f"{value:g}".replace(".", ",")
        return f"{formatted}{suffix}"

    for tick_index in range(tick_count + 1):
        amount = tick_index * scale_step
        y = plot_bottom + (amount / scale_maximum) * plot_height
        chart.add(Line(
            plot_left, y, plot_right, y,
            strokeColor=grid_color,
            strokeWidth=0.5,
        ))
        chart.add(String(
            plot_left - 6, y - 2.5, format_axis_amount(amount),
            fontName=font_name,
            fontSize=6,
            fillColor=colors.HexColor("#68736c"),
            textAnchor="end",
        ))

    slot_width = plot_width / period_count
    bar_width = min(28, slot_width * 0.68)
    for index, amount in enumerate(period_totals):
        bar_height = (amount / scale_maximum) * plot_height
        x = plot_left + index * slot_width + (slot_width - bar_width) / 2
        chart.add(Rect(
            x, plot_bottom, bar_width, bar_height,
            fillColor=chart_color,
            strokeColor=chart_color,
            strokeWidth=0,
        ))
        chart.add(String(
            plot_left + (index + 0.5) * slot_width,
            12,
            f"{index + 1:02d}",
            fontName=font_name,
            fontSize=6 if period_count > 20 else 7,
            fillColor=colors.HexColor("#183b32"),
            textAnchor="middle",
        ))

    chart.add(Line(
        plot_left, plot_bottom, plot_right, plot_bottom,
        strokeColor=colors.HexColor("#98a49b"),
        strokeWidth=0.8,
    ))

    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48,
        title=f"Thống kê thu nhập {year}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RevenueTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#183b32"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "RevenueSubtitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#426b59"),
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "RevenueDetailSection",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        textColor=colors.HexColor("#183b32"),
        spaceBefore=18,
        spaceAfter=10,
    )
    month_style = ParagraphStyle(
        "RevenueDetailMonth",
        parent=styles["Heading3"],
        fontName=font_name,
        fontSize=10,
        textColor=colors.HexColor("#426b59"),
        spaceBefore=8,
        spaceAfter=5,
    )
    total_style = ParagraphStyle(
        "RevenueTotal",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        spaceAfter=12,
    )
    table = Table(rows, colWidths=[320, 150], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f6f2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#183b32")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd5cf")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story = [
        Paragraph("THỐNG KÊ THU NHẬP", title_style),
        Paragraph(period_title, subtitle_style),
        chart,
        Spacer(1, 14),
        Paragraph(
            f"Tổng thu nhập: <b>{total_income:,}</b> đ".replace(",", "."),
            total_style,
        ),
        table,
    ]
    months_with_income = [
        (month_number, daily_totals)
        for month_number, daily_totals in sorted(monthly_daily_totals.items())
        if sum(daily_totals.values()) > 0
    ]
    if month is None and months_with_income:
        story.append(Paragraph("CHI TIẾT THU NHẬP THEO NGÀY", section_style))
        for month_number, daily_totals in months_with_income:
            days_in_month = monthrange(year, month_number)[1]
            daily_amounts = [
                daily_totals.get(day, 0)
                for day in range(1, days_in_month + 1)
            ]
            max_daily_total = max(daily_amounts, default=0)
            raw_daily_step = max_daily_total / 4 if max_daily_total else 250_000
            daily_scale_magnitude = 10 ** floor(log10(raw_daily_step))
            normalized_daily_step = raw_daily_step / daily_scale_magnitude
            daily_scale_step = (
                1 if normalized_daily_step <= 1
                else 2 if normalized_daily_step <= 2
                else 5 if normalized_daily_step <= 5
                else 10
            ) * daily_scale_magnitude
            daily_scale_maximum = max(
                4 * daily_scale_step,
                ceil(max_daily_total / daily_scale_step) * daily_scale_step,
            )
            daily_tick_count = round(daily_scale_maximum / daily_scale_step)
            detail_chart = Drawing(chart_width, 150)
            detail_left, detail_right = 42, chart_width - 8
            detail_bottom, detail_top = 25, 137
            detail_plot_width = detail_right - detail_left
            detail_plot_height = detail_top - detail_bottom

            for tick_index in range(daily_tick_count + 1):
                amount = tick_index * daily_scale_step
                y = detail_bottom + (amount / daily_scale_maximum) * detail_plot_height
                detail_chart.add(Line(
                    detail_left, y, detail_right, y,
                    strokeColor=grid_color,
                    strokeWidth=0.5,
                ))
                detail_chart.add(String(
                    detail_left - 6, y - 2.5, format_axis_amount(amount),
                    fontName=font_name,
                    fontSize=6,
                    fillColor=colors.HexColor("#68736c"),
                    textAnchor="end",
                ))

            daily_slot_width = detail_plot_width / days_in_month
            daily_bar_width = min(16, daily_slot_width * 0.68)
            for day, amount in enumerate(daily_amounts, start=1):
                x = detail_left + (day - 1) * daily_slot_width + (
                    daily_slot_width - daily_bar_width
                ) / 2
                bar_height = (amount / daily_scale_maximum) * detail_plot_height
                if amount > 0:
                    detail_chart.add(Rect(
                        x, detail_bottom, daily_bar_width, bar_height,
                        fillColor=chart_color,
                        strokeColor=chart_color,
                        strokeWidth=0,
                    ))
                detail_chart.add(String(
                    detail_left + (day - 0.5) * daily_slot_width,
                    9,
                    f"{day:02d}",
                    fontName=font_name,
                    fontSize=6,
                    fillColor=colors.HexColor("#183b32"),
                    textAnchor="middle",
                ))

            detail_chart.add(Line(
                detail_left, detail_bottom, detail_right, detail_bottom,
                strokeColor=colors.HexColor("#98a49b"),
                strokeWidth=0.8,
            ))
            story.extend([
                Paragraph(f"Tháng {month_number:02d}/{year}", month_style),
                Paragraph(
                    f"Tổng thu nhập tháng: "
                    f"<b>{sum(daily_totals.values()):,}</b> đ".replace(",", "."),
                    total_style,
                ),
                detail_chart,
                Spacer(1, 8),
            ])
    document.build(story)
    pdf_buffer.seek(0)
    filename = (
        f"thong-ke-thu-nhap-{year}-thang-{month:02d}.pdf"
        if month is not None
        else f"thong-ke-thu-nhap-{year}.pdf"
    )
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.post("/api/rentals/<int:rental_id>/checkout")
def checkout_rental(rental_id):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    ok, message, rental = room_service.checkout_rental(rental_id)
    return jsonify({"ok": ok, "message": message, "rental": rental}), 200 if ok else 400


@app.delete("/api/rentals/<int:rental_id>")
def delete_upcoming_rental(rental_id):
    if not session.get("user"):
        return jsonify({"ok": False, "message": "Vui lòng đăng nhập."}), 401
    ok, message = room_service.delete_upcoming_rental(rental_id)
    return jsonify({"ok": ok, "message": message}), 200 if ok else 400


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