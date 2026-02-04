from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from services.user_service import UserService


class RegisterView(QWidget):
    """View đăng ký tài khoản"""

    register_success = pyqtSignal()
    back_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.user_service = UserService() 
        self.init_ui()

    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Frame chính
        register_frame = QFrame()
        register_frame.setMaximumWidth(600)
        register_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        form_layout = QVBoxLayout(register_frame)

        # Tiêu đề
        title_label = QLabel("📝 ĐĂNG KÝ TÀI KHOẢN")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 24, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")

        subtitle_label = QLabel("Tạo tài khoản mới")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont('Arial', 12))
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")

        # Input style
        input_style = """
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
                min-height: 35px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """

        # Các trường nhập liệu
        def create_field(label_text, placeholder="", is_password=False):
            label = QLabel(label_text)
            label.setFont(QFont('Arial', 10))
            input_field = QLineEdit()
            input_field.setPlaceholderText(placeholder)
            input_field.setStyleSheet(input_style)
            if is_password:
                input_field.setEchoMode(QLineEdit.Password)
            return label, input_field

        fullname_label, self.fullname_input = create_field("Họ và tên: *", "Nhập họ và tên đầy đủ")
        username_label, self.username_input = create_field("Tên đăng nhập: *", "Ít nhất 3 ký tự")
        email_label, self.email_input = create_field("Email:", "email@example.com (không bắt buộc)")
        phone_label, self.phone_input = create_field("Số điện thoại:", "0123456789 (không bắt buộc)")
        password_label, self.password_input = create_field("Mật khẩu: *", "Ít nhất 6 ký tự", True)
        confirm_password_label, self.confirm_password_input = create_field("Xác nhận mật khẩu: *", "Nhập lại mật khẩu", True)

        # Ghi chú
        note_label = QLabel("* Trường bắt buộc")
        note_label.setFont(QFont('Arial', 9))
        note_label.setStyleSheet("color: #e74c3c; font-style: italic;")

        # Nút
        button_layout = QHBoxLayout()

        back_button = QPushButton("← Quay lại")
        back_button.setMinimumHeight(45)
        back_button.setFont(QFont('Arial', 11))
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        back_button.clicked.connect(self.handle_back)

        self.register_button = QPushButton("Đăng ký")
        self.register_button.setMinimumHeight(45)
        self.register_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.register_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        self.register_button.clicked.connect(self.handle_register)

        button_layout.addWidget(back_button, 35)
        button_layout.addWidget(self.register_button, 65)

        # Add widget vào layout
        for item in [
            title_label, subtitle_label, fullname_label, self.fullname_input,
            username_label, self.username_input, email_label, self.email_input,
            phone_label, self.phone_input, password_label, self.password_input,
            confirm_password_label, self.confirm_password_input, note_label
        ]:
            form_layout.addWidget(item)
            form_layout.addSpacing(10)

        form_layout.addLayout(button_layout)
        layout.addWidget(register_frame)

        # Style nền
        self.setStyleSheet("QWidget { background-color: #ecf0f1; }")
        self.setLayout(layout)

        # Enter để đăng ký
        self.confirm_password_input.returnPressed.connect(self.handle_register)

    def handle_register(self):
        """Xử lý đăng ký tài khoản"""
        full_name = self.fullname_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validation cơ bản (UI)
        if not full_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập họ tên!")
            self.fullname_input.setFocus()
            return
        if not username:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập!")
            self.username_input.setFocus()
            return
        if not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mật khẩu!")
            self.password_input.setFocus()
            return
        if password != confirm_password:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không khớp!")
            self.confirm_password_input.setFocus()
            self.confirm_password_input.selectAll()
            return
        if email and '@' not in email:
            QMessageBox.warning(self, "Lỗi", "Email không hợp lệ!")
            self.email_input.setFocus()
            return

        # Gọi service để xử lý đăng ký
        try:
            user_id = self.user_service.register_user(
                username=username,
                password=password,
                full_name=full_name,
                email=email,
                phone=phone
            )

            QMessageBox.information(
                self,
                "Thành công",
                f"✅ Đăng ký thành công!\n\n"
                f"Tài khoản: {username}\n"
                f"Họ tên: {full_name}\n\n"
                f"Vui lòng đăng nhập để tiếp tục."
            )
            self.clear_form()
            self.register_success.emit()

        except ValueError as e:
            QMessageBox.warning(self, "Lỗi đăng ký", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi hệ thống", f"Đã xảy ra lỗi:\n{e}")

    def handle_back(self):
        """Quay lại màn hình đăng nhập"""
        self.clear_form()
        self.back_to_login.emit()

    def clear_form(self):
        """Xóa dữ liệu form"""
        self.fullname_input.clear()
        self.username_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
