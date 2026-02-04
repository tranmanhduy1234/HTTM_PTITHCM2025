import sys
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt
from views.LoginView import LoginView
from views.register_view import RegisterView
from views.DashboardView import DashboardView
from utils.sound_manager import cleanup_sound_manager
from services.session_service import SessionService


class MainWindow(QMainWindow):
    """Main Window - Lazy load views"""

    def __init__(self):
        super().__init__()
        self.session_service = None
        self.current_session_id = None
        self.setWindowTitle("Hệ thống cảnh báo buồn ngủ")

        # self.setGeometry(100, 100, 1200, 300)
        self.setGeometry(100, 50, 1000, 650)  # Giảm từ 1200x700
        self.setMinimumSize(900, 600)  # Kích thước tối thiểu

        # Database
        self.current_user = None
    
        # Stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize only essential views
        self.init_essential_views()

        # Lazy-loaded views
        self.statistics_view = None
        self.video_review_view = None

        # Show login
        self.show_login()

    def init_essential_views(self):
        """Chỉ init views cần thiết"""
        print("📦 Khởi tạo views cơ bản...")

        # Login View
        self.login_view = LoginView()
        self.login_view.login_success.connect(self.show_dashboard)
        self.login_view.register_clicked.connect(self.show_register)

        # Register View
        self.register_view = RegisterView()
        self.register_view.register_success.connect(self.show_login)
        self.register_view.back_to_login.connect(self.show_login)

        # Dashboard View
        self.dashboard_view = DashboardView()
        # self.dashboard_view.set_database(self.db)

        self.dashboard_view.logout_signal.connect(self.show_login)
        self.dashboard_view.statistics_signal.connect(self.show_statistics)
        self.dashboard_view.videos_signal.connect(self.show_videos)

        # Add to stack
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.register_view)
        self.stacked_widget.addWidget(self.dashboard_view)

        print("✅ Views cơ bản đã sẵn sàng")

    def _ensure_statistics_view(self):
        """Lazy load statistics view"""
        if self.statistics_view is None:
            print("📊 Đang tải Statistics View...")
            try:
                from views.statistics_view import StatisticsView
                self.statistics_view = StatisticsView()
                self.statistics_view.back_signal.connect(self.show_dashboard_from_stats)
                self.stacked_widget.addWidget(self.statistics_view)
                print("✅ Statistics View đã sẵn sàng")
            except Exception as e:
                print(f"❌ Lỗi load Statistics View: {e}")
                import traceback
                traceback.print_exc()
                return False
        return True

    def _ensure_video_review_view(self):
        """Lazy load video review view"""
        if self.video_review_view is None:
            print("🎬 Đang tải Video Review View...")
            try:
                from views.video_review_view import VideoReviewView
                self.video_review_view = VideoReviewView()
                self.video_review_view.back_signal.connect(self.show_dashboard_from_videos)
                self.stacked_widget.addWidget(self.video_review_view)
                print("✅ Video Review View đã sẵn sàng")
            except Exception as e:
                print(f"❌ Lỗi load Video Review View: {e}")
                import traceback
                traceback.print_exc()
                return False
        return True

    def show_login(self):

        """Chuyển sang màn hình đăng nhập"""
        # Nếu có session đang chạy thì kết thúc
        if self.current_session_id and self.session_service:
            self.session_service.end_session()
            self.current_session_id = None

        self.stacked_widget.setCurrentWidget(self.login_view)
        self.setWindowTitle("Đăng nhập - Hệ thống cảnh báo buồn ngủ")
        self.current_user = None

    def show_register(self):
        """Chuyển sang đăng ký"""
        self.stacked_widget.setCurrentWidget(self.register_view)
        self.setWindowTitle("Đăng ký tài khoản")

    def show_dashboard(self, user_info):
        """Chuyển sang dashboard"""
        self.current_user = user_info
        self.session_service = SessionService(user_info["id"])
        self.current_session_id = self.session_service.start_session()

        # Gửi user + session sang DashboardView
        self.dashboard_view.set_user_info(user_info)
        self.dashboard_view.set_session_info(self.current_session_id)

        self.stacked_widget.setCurrentWidget(self.dashboard_view)
        self.setWindowTitle(f"Dashboard - {user_info['full_name']}")

    def show_dashboard_from_stats(self):
        """Quay lại dashboard từ statistics"""
        if self.current_user:
            self.stacked_widget.setCurrentWidget(self.dashboard_view)
            self.setWindowTitle(f"Dashboard - {self.current_user['full_name']}")

    def show_dashboard_from_videos(self):
        """Quay lại dashboard từ videos"""
        if self.current_user:
            self.stacked_widget.setCurrentWidget(self.dashboard_view)
            self.setWindowTitle(f"Dashboard - {self.current_user['full_name']}")

    def show_statistics(self):
        """Chuyển sang statistics - LAZY LOAD"""
        if not self.current_user:
            return

        if not self._ensure_statistics_view():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", "Không thể tải trang Thống kê!")
            return

        try:
            self.statistics_view.set_user_info(self.current_user)
            self.stacked_widget.setCurrentWidget(self.statistics_view)
            self.setWindowTitle(f"Thống kê - {self.current_user['full_name']}")
        except Exception as e:
            print(f"❌ Lỗi hiển thị statistics: {e}")

    def show_videos(self):
        """Chuyển sang videos - LAZY LOAD"""
        if not self.current_user:
            return

        if not self._ensure_video_review_view():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", "Không thể tải trang Xem video!")
            return

        try:
            self.video_review_view.set_user_info(self.current_user)
            self.stacked_widget.setCurrentWidget(self.video_review_view)
            self.setWindowTitle(f"Xem video - {self.current_user['full_name']}")
        except Exception as e:
            print(f"❌ Lỗi hiển thị videos: {e}")

    def closeEvent(self, event):
        """Xử lý khi đóng"""
        print("\n🔄 Đang đóng ứng dụng...")

        try:
            # Dừng camera
            if hasattr(self.dashboard_view, 'camera_thread') and self.dashboard_view.camera_thread:
                print("📹 Đang dừng camera...")
                self.dashboard_view.stop_monitoring()

            # Cleanup sound
            print("🔇 Đang dừng âm thanh...")
            cleanup_sound_manager()

            # Đóng database
            # print("💾 Đang đóng database...")
            # self.db.close()

            print("✅ Đã đóng an toàn\n")
            if hasattr(self.dashboard_view, 'camera_thread') and self.dashboard_view.camera_thread:
                self.dashboard_view.stop_monitoring()

                # Kết thúc session nếu còn
            if self.current_session_id and self.session_service:
                print("🧾 Kết thúc session...")
                self.session_service.end_session()

        except Exception as e:
            print(f"⚠️ Lỗi khi đóng: {e}")
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    print("=" * 60)
    print("🚀 HỆ THỐNG CẢNH BÁO BUỒN NGỦ")
    print("=" * 60)
    print()

    try:
        window = MainWindow()
        window.show()

        exit_code = app.exec_()

        print("\n" + "=" * 60)
        cleanup_sound_manager()
        print("=" * 60)

        sys.exit(exit_code)

    except Exception as e:
        print(f"\n❌ LỖI KHỞI ĐỘNG: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()