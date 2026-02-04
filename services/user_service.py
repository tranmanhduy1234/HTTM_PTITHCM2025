# services/user_service.py
import re
from repository import user_repo, session_repo


class UserService:
    """Xử lý nghiệp vụ liên quan đến người dùng"""

    # ----------- VALIDATION -----------

    def validate_email(self, email: str):
        """Kiểm tra định dạng email hợp lệ"""
        if not email:
            return True  # Cho phép bỏ trống
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    def validate_password(self, password: str):
        """Kiểm tra password đủ mạnh"""
        if len(password) < 6:
            return "Mật khẩu phải có ít nhất 6 ký tự"
        if password.isdigit() or password.isalpha():
            return "Mật khẩu nên chứa cả chữ và số"
        return None

    # ----------- ĐĂNG KÝ -----------

    def register_user(self, username, password, full_name, email="", phone=""):
        """Đăng ký user mới"""
        username = username.strip()
        full_name = full_name.strip()
        email = email.strip()

        # Kiểm tra trống
        if not username or not password or not full_name:
            raise ValueError("Vui lòng nhập đầy đủ họ tên, tên đăng nhập và mật khẩu.")

        # Kiểm tra trùng username
        if user_repo.username_exists(username):
            raise ValueError("Tên đăng nhập đã tồn tại!")

        # Kiểm tra email trùng
        if email and user_repo.email_exists(email):
            raise ValueError("Email đã được sử dụng!")

        # Kiểm tra định dạng email
        if email and not self.validate_email(email):
            raise ValueError("Định dạng email không hợp lệ!")

        # Kiểm tra độ mạnh mật khẩu
        pw_check = self.validate_password(password)
        if pw_check:
            raise ValueError(pw_check)

        # Mã hoá mật khẩu
        password_hash = user_repo.hash_password(password)

        # Lưu DB
        user_id = user_repo.insert_user(full_name, username, password_hash, email, phone)
        return user_id

    # ----------- ĐĂNG NHẬP -----------

    def login_user(self, username: str, password: str):
        """Đăng nhập người dùng"""
        if not username or not password:
            raise ValueError("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!")

        user = user_repo.get_user_by_username(username)
        if not user:
            return None  # user không tồn tại

        # Hash mật khẩu nhập vào rồi so sánh
        password_hash = user_repo.hash_password(password)
        if password_hash != user["password"]:
            return None

        # Nếu đúng, trả về thông tin user
        return {
            "id": user["id"],
            "username": user["userName"],
            "full_name": user.get("fullName", ""),
            "email": user.get("email", ""),
            "phone": user.get("phone", ""),
            "created_at": user.get("createdAt", "")
        }

    def get_user_info_by_session(self, session_id: int):
        if not session_id:
            return None
            
        user_id = session_repo.get_user_id_by_session_id(session_id)
        
        if not user_id:
            return None
            
        user = user_repo.get_user_by_id(user_id)
        
        if not user:
            return None

        return {
            "id": user["id"],
            "username": user["userName"],
            "email": user.get("email", ""),
            "created_at": user.get("createdAt", ""),
            "is_active": user.get("isActive", 1)
        }