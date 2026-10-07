# Lotus Stay - Quản lý khách sạn

Ứng dụng Flask độc lập, sử dụng SQLite để lưu tài khoản và session để giữ trạng thái đăng nhập.

## Chức năng hiện có

- Đăng nhập bằng email và mật khẩu.
- Báo lỗi khi email hoặc mật khẩu không đúng.
- Khôi phục mật khẩu bằng mã xác minh gửi qua email.
- Duy trì trạng thái đăng nhập bằng session; tải lại trang không làm mất phiên.
- Đăng xuất và xóa session.
- Xem và cập nhật họ tên, ngày sinh, số điện thoại, ảnh đại diện; email không thể chỉnh sửa.

## Chạy ứng dụng

Cần [Python 3.10 trở lên](https://www.python.org/downloads/). Mở PowerShell tại thư mục dự án và chạy:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Mở http://127.0.0.1:5000.

Lần chạy đầu tự tạo `hotel_management.db` cùng tài khoản quản lý mẫu:

- Email: `admin@lotusstay.local`
- Mật khẩu: `Hotel@123`

Mật khẩu được lưu dưới dạng hash trong SQLite. Thay `SECRET_KEY` bằng giá trị riêng khi triển khai ngoài môi trường phát triển.

## Cấu hình gửi email

Để bật khôi phục mật khẩu, cấu hình SMTP trước khi chạy ứng dụng. Ví dụ trong PowerShell:
https://myaccount.google.com/apppasswords
```powershell
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-address@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
$env:SMTP_FROM = "your-address@gmail.com"
$env:SMTP_USE_TLS = "true"
python app.py
```

Mã xác minh có hiệu lực 10 phút, chỉ được dùng một lần và tối đa 5 lần nhập sai. Mỗi email chỉ có thể yêu cầu gửi lại mã sau 60 giây.