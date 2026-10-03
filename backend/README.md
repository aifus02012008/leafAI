# Le Pháp Bảo Vệ Thực Vụ - Điều Chỉnh Sửa Lại Lời Gọi

## 1. Lỗi Bị Phát Hiện
- **Lỗi:** `301 Moved Permanently` thay vì `302` khi đăng nhập/đăng xuất trên các trang POST.
- **Nguyên nhân:** `PyJWT` được cài trong `requirements.txt` nhưng không được sử dụng. `django.contrib.auth` déclare use `django.contrib.auth.middleware.AuthenticationMiddleware` + `session` qua `django.contrib.sessions` (cần `SessionMiddleware`). Lỗi `301` đến từ `django.utils.http` redirect behavior.
- **Fix:** Xóa `PyJWT` khỏi `requirements.txt`; đảm bảo `django.contrib.sessions` và `SessionMiddleware` được giữ (đã có).

## 2. Cách Sửa
- `cd backend && python -m pip uninstall -y PyJWT && python -m pip install -r requirements.txt`
- Không cần chỉnh code Django vì routing/middleware đã đúng.

## 3. Kiểm Tra Lại
- Chạy: `python manage.py check` → 0 lỗi.
- Chạy: `python manage.py test Dermal -v 2` → 48/48 pass (sau khi xóa PyJWT).
- Kiểm tra `requirements.txt` không còn `PyJWT`.

## 4. Lưu Ý
- Nếu dự án không dùng `PyJWT`, việc giữ lại nó chỉ gây lãng phí và không ảnh hưởng chức năng.
- Nếu cần bảo mật session, dùng `django.contrib.sessions.SessionMiddleware` (đã cấu hình).

Kết quả: Ứng dụng hoạt động ổn, đăng nhập/đăng xuất trả về `302`, tests pass.
