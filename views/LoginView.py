from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QCursor
from services.user_service import UserService
from views.Dialogs import WaitingDialog
import time
class LoginView(QWidget):
    """View đăng nhập"""

    # Signal phát ra khi đăng nhập thành công
    login_success = pyqtSignal(dict)  # Truyền user_info
    register_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.user_service = UserService()
        self.init_ui()

    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Frame chứa form đăng nhập
        login_frame = QFrame()
        login_frame.setMaximumWidth(500)
        login_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        form_layout = QVBoxLayout(login_frame)

        # Logo/Tiêu đề
        title_label = QLabel("🚗 HỆ THỐNG CẢNH BÁO")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 24, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        # Tạo thẻ trạng thái
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d; 
                font-size: 14px; 
                background-color: #ecf0f1;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        subtitle_label = QLabel("Giám sát buồn ngủ khi lái xe")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont('Arial', 12))
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")

        # Username field
        username_label = QLabel("Tên đăng nhập:")
        username_label.setFont(QFont('Arial', 10))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nhập tên đăng nhập")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)

        # Password field
        password_label = QLabel("Mật khẩu:")
        password_label.setFont(QFont('Arial', 10))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)

        # Login button
        self.login_button = QPushButton("Đăng nhập")
        self.login_button.setMinimumHeight(45)
        self.login_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)

        # Register link
        register_layout = QHBoxLayout()
        register_text = QLabel("Chưa có tài khoản?")
        register_text.setFont(QFont('Arial', 10))
        register_text.setStyleSheet("color: #7f8c8d;")

        self.register_link = QLabel('<a href="#" style="color: #3498db; text-decoration: none;">Đăng ký ngay</a>')
        self.register_link.setFont(QFont('Arial', 10, QFont.Bold))
        self.register_link.setCursor(QCursor(Qt.PointingHandCursor))
        self.register_link.linkActivated.connect(self.handle_register_click)

        register_layout.addStretch()
        register_layout.addWidget(register_text)
        register_layout.addWidget(self.register_link)
        register_layout.addStretch()

        # Thêm các widget vào layout
        form_layout.addWidget(title_label)
        form_layout.addWidget(subtitle_label)
        form_layout.addSpacing(20)
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addSpacing(15)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(25)
        form_layout.addWidget(self.login_button)
        form_layout.addSpacing(15)
        form_layout.addLayout(register_layout)
        form_layout.addSpacing(10)
        # form_layout.addWidget(demo_info)

        layout.addWidget(login_frame)

        # Set background cho toàn bộ view
        self.setStyleSheet("QWidget { background-color: #ecf0f1; }")
        self.setLayout(layout)

        # Enter để login
        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        """Xử lý đăng nhập"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        # Cho phép admin mặc định
        if username == "admin" and password == "admin":
            user_info = {
                'id': 0,
                'username': 'admin',
                'full_name': 'Administrator',
                'email': 'admin@system.local',
                'phone': '',
                'created_at': 'Default Account'
            }
            # Hiển thị waiting dialog và thực hiện xử lý
            self.show_waiting_and_process(user_info)
            return
        
        try:
            user_info = self.user_service.login_user(username, password)
            if user_info:
                # Hiển thị waiting dialog và thực hiện xử lý
                self.show_waiting_and_process(user_info)
                self.clear_form()
            else:
                QMessageBox.warning(self, "Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng!")
        except Exception as e:
            QMessageBox.critical(self, "CÓ cái lol", str(e))

    def handle_register_click(self):
        """Xử lý khi click vào link đăng ký"""
        self.clear_form()
        self.register_clicked.emit()

    def clear_form(self):
        """Xóa form sau khi đăng nhập"""
        self.username_input.clear()
        self.password_input.clear()
    
    def process_after_login(self, user_info):
        print(user_info)
        # if, thời gian hiện tại...
        threadTraining(user_info["id"])
        return True
    
    def show_waiting_and_process(self, user_info):
        """Hiển thị dialog chờ và thực hiện xử lý"""
        # Tạo waiting dialog với hàm xử lý
        waiting_dialog = WaitingDialog(
            parent=self,
            process_function=self.process_after_login,
            user_info=user_info
        )
        
        # Hiển thị dialog và chờ xử lý xong
        if waiting_dialog.exec_() == WaitingDialog.Accepted:
            # Nếu xử lý thành công, mới emit signal để chuyển sang dashboard
            self.login_success.emit(user_info)
        else:
            # Nếu có lỗi, hiển thị thông báo
            QMessageBox.warning(self, "Lỗi", "Có lỗi xảy ra trong quá trình xử lý!")
            

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import db.db as database
from ultralytics import YOLO

class ModelTrainer:
    """Lớp quản lý việc train model phát hiện buồn ngủ"""
    
    def __init__(self, base_dir: str = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025"):
        self.base_dir = Path(base_dir)
        self.source_training = self.base_dir / "drowsy_images"
        self.tmp_dataset = self.base_dir / "tmp_dataset"
        
        # Định nghĩa các đường dẫn
        self.train_drowsy = self.tmp_dataset / "train" / "Drowsy"
        self.train_natural = self.tmp_dataset / "train" / "Natural"
        self.test_drowsy = self.tmp_dataset / "test" / "Drowsy"
        self.test_natural = self.tmp_dataset / "test" / "Natural"
        
        self.train_test_split = 0.8
        
    def clear_folder(self, path: Path) -> None:
        """Xóa và tạo lại thư mục rỗng"""
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        
    def prepare_directories(self) -> None:
        """Chuẩn bị các thư mục cần thiết"""
        print("Đang chuẩn bị thư mục...")
        for directory in [self.train_drowsy, self.train_natural, 
                         self.test_drowsy, self.test_natural]:
            self.clear_folder(directory)
        print("Hoàn tất chuẩn bị thư mục")
        
    def get_latest_session_folder(self, session_id) -> Optional[Path]:
        if not self.source_training.exists():
            print(f"Thư mục {self.source_training} không tồn tại")
            return None
        folders = [
            f for f in os.listdir(self.source_training)
            if not os.path.isfile(f) and f.endswith(str(session_id))
        ]
        if not folders:
            print("Không tìm thấy folder nào trong thư mục training")
            return None
        latest_folder = folders
        print(f"Folder training mới nhất: {latest_folder}")
        return latest_folder
        
    def collect_images(self, folder_paths: Path) -> Tuple[List[Path], List[Path]]:
        """Thu thập các ảnh Drowsy và Natural từ folder"""
        drowsy_images = []
        natural_images = []
        for folder_path in folder_paths:
            if not folder_path or not os.path.exists(os.path.join(self.source_training, folder_path)):
                return drowsy_images, natural_images
            
            folder_path_full = os.path.join(self.source_training, folder_path)
            for image_file in os.listdir(folder_path_full):
                if not image_file.endswith(".jpg"):
                    continue
                    
                if "Drowsy" in image_file:
                    drowsy_images.append(os.path.join(folder_path_full, image_file))
                elif "Natural" in image_file:
                    natural_images.append(os.path.join(folder_path_full, image_file))
                
        return drowsy_images, natural_images
        
    def balance_dataset(self, drowsy: List[Path], natural: List[Path]) -> Tuple[List[Path], List[Path]]:
        """Cân bằng số lượng ảnh giữa 2 class"""
        min_length = min(len(drowsy), len(natural))
        return drowsy[:min_length], natural[:min_length]
        
    def split_and_copy_images(self, drowsy: List[Path], natural: List[Path]) -> None:
        """Chia dataset thành train/test và copy ảnh"""
        split_idx = int(len(drowsy) * self.train_test_split)
        
        print(f"Đang copy {split_idx} ảnh train cho mỗi class...")
        print(f"Đang copy {len(drowsy) - split_idx} ảnh test cho mỗi class...")
        
        # Copy train set
        self._copy_images(drowsy[:split_idx], self.train_drowsy)
        self._copy_images(natural[:split_idx], self.train_natural)
        
        # Copy test set
        self._copy_images(drowsy[split_idx:], self.test_drowsy)
        self._copy_images(natural[split_idx:], self.test_natural)
        
        print("Hoàn tất copy ảnh")
        
    def _copy_images(self, image_list: List[Path], dest_dir: Path) -> None:
        """Copy danh sách ảnh vào thư mục đích"""
        for img_path in image_list:
            dest_path = dest_dir / os.path.basename(img_path)
            shutil.copy2(img_path, dest_path)
            
    def get_model_path(self, user_id: int) -> Path:
        """Lấy đường dẫn model của user"""
        return self.base_dir / "model"/f"model_{user_id}.pt"
        
    def train_model(self, user_id: int, epochs: int = 1, imgsz: int = 640) -> str:
        """Train model YOLO"""
        print(f"\nBắt đầu train model cho user {user_id}...")
        
        model_path = self.get_model_path(user_id)
        # Load model cũ nếu có, không thì load pretrained
        if model_path.exists():
            print(f"Sử dụng model cũ: {model_path}")
            model = YOLO(str(model_path))
        else:
            print("Sử dụng model pretrained: yolo11n-cls.pt")
            model = YOLO("yolo11n-cls.pt")
            
        # Train model
        results = model.train(
            data=str(self.tmp_dataset),
            epochs=epochs,
            imgsz=imgsz,
            verbose=True
        )
        
        print(f"\nKết quả train được lưu tại: {results.save_dir}")
        save_dir = results.save_dir
        return save_dir
        
    def run_training_pipeline(self, session_id: int, user_id: int) -> None:
        """Chạy toàn bộ pipeline training"""
        try:
            # 1. Chuẩn bị thư mục
            self.prepare_directories()
            
            # 2. Lấy folder training mới nhất
            training_folders = self.get_latest_session_folder(session_id)
            if not training_folders:
                print("Không tìm thấy dữ liệu training")
                return
            
            # 3. Thu thập ảnh, 2 arr chứa đường dẫn các ảnh, đường dẫn đầy đủ.
            drowsy, natural = self.collect_images(training_folders)
            print(f"Tìm thấy: {len(drowsy)} ảnh Drowsy, {len(natural)} ảnh Natural")
            
            if not drowsy or not natural:
                print("Không đủ dữ liệu để training")
                return
                
            # 4. Cân bằng dataset
            drowsy, natural = self.balance_dataset(drowsy, natural)
            print(f"Dataset sau khi cân bằng: {len(drowsy)} ảnh mỗi class")
            
            # 5. Chia và copy ảnh
            self.split_and_copy_images(drowsy, natural)
            
            # 6. Train model
            save_dir = self.train_model(user_id)
            
            print("\n✓ Hoàn tất quá trình training!")
            print(f"\n✓ Kết quả lưu tại {save_dir}")
            
            path_new_model = save_dir / "weights" / "best.pt"
            if os.path.exists(path_new_model):
                print(f"\n✓ Tìm thấy đường dẫn file kết quả model tại: {path_new_model}")
                path_old_model = self.get_model_path(user_id)
                
                try:
                    os.remove(path_old_model)
                except Exception as e:
                    print(e)
                    print(f"\n Model đầu tiên của user mang ID: {user_id}")
                shutil.copy(path_new_model, path_old_model)
            else:
                print("Lỗi đường dẫn file model kết quả")
            
        except Exception as e:
            print(f"✗ Lỗi trong quá trình training: {str(e)}")
            raise

def get_latest_session_id(user_id: str) -> Optional[int]:
    """Lấy session ID mới nhất của user từ database"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ID, userID 
            FROM Session
            WHERE userID = ?
            ORDER BY ID DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        print("Lấy session ID cuối thành công")
        return row[0] if row else None
        
    except Exception as e:
        print(f"Lỗi khi truy vấn database: {str(e)}")
        return None

def threadTraining(user_id):
    # Lấy session ID mới nhất (nếu cần)
    session_id = get_latest_session_id(user_id)
    if session_id:
        print(f"Session ID mới nhất: {session_id}")
    base_dir = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025"
    # Khởi tạo trainer và chạy
    trainer = ModelTrainer(base_dir=base_dir)
    trainer.run_training_pipeline(int(session_id), user_id=int(user_id))