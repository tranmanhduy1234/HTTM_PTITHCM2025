from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QMessageBox, QFileDialog,
                             QScrollArea, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QDateTime, QSize
from PyQt5.QtGui import QFont, QColor, QPixmap
from views.Dialogs import DrowsinessAlertDialog, RestAlertDialog

import os
import traceback
import core.config as config


class DashboardView(QWidget):
    logout_signal = pyqtSignal()
    statistics_signal = pyqtSignal()  # MỚI
    videos_signal = pyqtSignal()  # MỚI

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.start_time = None
        self.drowsiness_count = 0
        self.last_drowsiness_time = None
        self.drowsiness_window = 300  # 5 minutes
        self.camera_thread = None
        self.detector = None
        self.current_alert_timestamp = None
        self.current_session_id = None
        self.model_path = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(5)
        camera_widget = self.create_camera_view()
        content_layout.addWidget(camera_widget, 60)
        log_widget = self.create_log_view()
        content_layout.addWidget(log_widget, 40)

        main_layout.addLayout(content_layout, 1)
        self.setLayout(main_layout)

    def create_header(self):
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.user_label = QLabel("👤 Người dùng: ")
        self.user_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.user_label.setStyleSheet("color: #2c3e50;")

        self.drive_time_label = QLabel("⏱️ 00:00:00")
        self.drive_time_label.setFont(QFont('Arial', 10))
        self.drive_time_label.setStyleSheet("color: #27ae60;")

        # NÚT MỚI: Thống kê
        stats_button = QPushButton("📊 Thống kê")
        stats_button.setMaximumHeight(35)
        stats_button.setMinimumWidth(100)
        stats_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        stats_button.clicked.connect(self.show_statistics)

        # NÚT MỚI: Xem video
        video_button = QPushButton("🎬 Xem video")
        video_button.setMaximumHeight(35)
        video_button.setMinimumWidth(100)
        video_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        video_button.clicked.connect(self.show_videos)

        # Nút bắt đầu/kết thúc
        self.start_button = QPushButton("🚗 Bắt đầu")
        self.start_button.setMaximumHeight(35)
        self.start_button.setMinimumWidth(120)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.start_button.clicked.connect(self.toggle_monitoring)

        logout_button = QPushButton("🚪 Đăng xuất")
        logout_button.setMaximumHeight(35)
        logout_button.setMinimumWidth(100)
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_button.clicked.connect(self.handle_logout)

        layout.addWidget(self.user_label)
        layout.addWidget(self.drive_time_label)
        layout.addStretch()
        layout.addWidget(stats_button)  # NÚT MỚI
        layout.addWidget(video_button)  # NÚT MỚI
        layout.addWidget(self.start_button)
        layout.addWidget(logout_button)
        return layout

    def create_camera_view(self):
        group = QGroupBox("📹 Camera giám sát")
        group.setFont(QFont('Arial', 10, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                color: #2c3e50;
                subcontrol-origin: margin;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 15, 8, 8)

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera_label.setMinimumSize(400, 300)
        self.camera_label.setScaledContents(False)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                border-radius: 5px;
                color: white;
                font-size: 14px;
            }
        """)
        self.camera_label.setText("📷\n\nCamera chưa hoạt động\n\nNhấn 'Bắt đầu' để khởi động")

        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        self.status_label = QLabel("⚫ Chưa hoạt động")
        self.status_label.setFont(QFont('Arial', 9))
        self.alert_count_label = QLabel("⚠️ 0/3")
        self.alert_count_label.setFont(QFont('Arial', 9))
        self.alert_count_label.setStyleSheet("color: #27ae60;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.alert_count_label)

        layout.addWidget(self.camera_label, 1)
        layout.addLayout(status_layout)
        group.setLayout(layout)
        return group

    def create_log_view(self):
        group = QGroupBox("📋 Nhật ký")
        group.setFont(QFont('Arial', 10, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                color: #2c3e50;
                subcontrol-origin: margin;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 15, 8, 8)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(['Giờ', 'TG lái', 'Trạng thái'])
        self.log_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                gridline-color: #ecf0f1;
                font-size: 9px;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
                font-size: 9px;
            }
        """)
        self.log_table.verticalHeader().setDefaultSectionSize(25)
        self.log_table.verticalHeader().setVisible(False)
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        clear_button = QPushButton("🗑️")
        clear_button.setMaximumWidth(40)
        clear_button.setMaximumHeight(28)
        clear_button.setToolTip("Xóa log")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        clear_button.clicked.connect(self.clear_log)

        load_button = QPushButton("📥 Tải DB")
        load_button.setMaximumHeight(28)
        load_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        load_button.clicked.connect(self.load_logs_from_db)

        button_layout.addWidget(load_button)
        button_layout.addWidget(clear_button)

        layout.addWidget(self.log_table, 1)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def set_user_info(self, user_info):
        self.current_user = user_info
        full_name = user_info['full_name']
        if len(full_name) > 20:
            full_name = full_name[:17] + "..."
        self.user_label.setText(f"👤 {full_name}")

    def set_session_info(self, session_id):
        self.current_session_id = session_id

    def toggle_monitoring(self):
        if self.start_time is None:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        try:
            if not self.model_path or not os.path.exists(self.model_path):
                # self.model_path = self.select_model_path()
                print(self.current_user)
                self.model_path = fr"{config.config.get("model_path")}\model_{self.current_user["id"]}.pt"
            if not self.model_path:
                return

            from core.DrowsinessDetector import DrowsinessDetector
            from utils.CameraThread import CameraThread

            print(
                f"🔧 Initializing detector with user_id={self.current_user['id']}, session_id={self.current_session_id}")
            self.detector = DrowsinessDetector(
                model_path=self.model_path,
                batch_size=4,
                alert_threshold=3,
                session_id=self.current_session_id,
            )
            print("✅ Detector initialized")

            self.camera_thread = CameraThread(self.detector, camera_source=config.config.get("camera", 0)['source'])
            self.camera_thread.frame_ready.connect(self.update_camera_frame)
            self.camera_thread.drowsiness_alert.connect(self.handle_drowsiness_alert)
            self.camera_thread.error_occurred.connect(self.handle_camera_error)
            self.camera_thread.start()
            print("✅ Camera started")

            self.start_time = QDateTime.currentDateTime()
            self.start_button.setText("⏹️ Dừng")
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.status_label.setText("🟢 Đang giám sát")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_drive_time)
            self.update_timer.start(1000)

            print("✅ System started")

        except Exception as e:
            error_msg = f"❌ Error starting: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            print(f"Error: {e}\n{traceback.format_exc()}")
            self.stop_monitoring()

    def select_model_path(self):
        default_paths = [
            r"core\best.pt",
            r"best.pt",
            r"models\best.pt"
        ]
        for path in default_paths:
            if os.path.exists(path):
                reply = QMessageBox.question(
                    self, 'Model YOLO',
                    f'Use:\n{path}?',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    return path

        path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLO model (best.pt)", "", "Model Files (*.pt);;All Files (*)"
        )
        if path and os.path.exists(path):
            return path
        elif path:
            QMessageBox.warning(self, "Error", f"File does not exist:\n{path}")
        return None

    def stop_monitoring(self):
        try:
            print("🛑 Stopping...")
            if self.camera_thread:
                print("📹 Stopping camera...")
                self.camera_thread.stop()
                self.camera_thread.wait(3000)
                self.camera_thread = None

            if self.detector:
                print("🔧 Stopping detector...")
                self.detector.stop()
                self.detector = None

            if hasattr(self, 'update_timer'):
                self.update_timer.stop()

        except Exception as e:
            print(f"Error stopping: {e}")

        finally:
            self.start_time = None
            self.start_button.setText("🚗 Bắt đầu")
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            self.camera_label.setText("📷\n\nCamera đã tắt\n\nNhấn 'Bắt đầu' để khởi động")
            self.camera_label.setPixmap(QPixmap())
            self.camera_label.setStyleSheet("""
                QLabel {
                    background-color: #34495e;
                    border: 2px solid #2c3e50;
                    border-radius: 5px;
                    color: white;
                    font-size: 14px;
                }
            """)
            self.status_label.setText("⚫ Đã dừng")
            self.status_label.setStyleSheet("color: #7f8c8d;")
            self.drive_time_label.setText("⏱️ 00:00:00")
            self.drowsiness_count = 0
            self.update_alert_count()
            print("✅ Stopped")

    def update_camera_frame(self, pixmap, status):
        try:
            scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.camera_label.setPixmap(scaled_pixmap)
            if status['alert_active']:
                self.status_label.setText("🔴 CẢNH BÁO!")
                self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                class_name = status['class']
                if class_name.lower() == 'drowsy':
                    self.status_label.setText(f"🟡 {class_name}")
                    self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                else:
                    self.status_label.setText(f"🟢 {class_name}")
                    self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        except Exception as e:
            print(f"Error updating frame: {e}")

    def handle_drowsiness_alert(self, drowsy_ratio, confidence):
        """Xử lý cảnh báo buồn ngủ"""
        crurent_id = self.detector.current_frame_id
        dialog = DrowsinessAlertDialog(self, current_id=crurent_id)
        result = dialog.exec_()

        current_time = QDateTime.currentDateTime()
        drive_time = self.drive_time_label.text().replace("⏱️ ", "")

        # Lưu timestamp để cập nhật DB sau
        self.current_alert_timestamp = current_time.toString(Qt.ISODate)

        if result == DrowsinessAlertDialog.Accepted:
            # User XÁC NHẬN buồn ngủ
            print("✅ User xác nhận: BUỒN NGỦ")
            self.add_log(current_time.toString("HH:mm:ss"), drive_time, "✅ Xác nhận buồn ngủ")

            # Cập nhật DB
            if self.detector:
                try:
                    self.detector.update_alert_confirmation(
                        dialog.current_id,
                        confirmed=True,
                        # notes="Người dùng xác nhận buồn ngủ"
                    )
                except:
                    pass

            # Đếm số lần buồn ngủ
            if self.last_drowsiness_time is None or \
                    self.last_drowsiness_time.secsTo(current_time) > self.drowsiness_window:
                self.drowsiness_count = 1
            else:
                self.drowsiness_count += 1

            self.last_drowsiness_time = current_time
            self.update_alert_count()

            # Kiểm tra cần nghỉ ngơi
            if self.drowsiness_count >= 3:
                self.show_rest_alert()

        else:
            if hasattr(dialog, 'is_timeout') and dialog.is_timeout:
                # TIMEOUT - Bỏ qua
                print("⏱️ Timeout: BỎ QUA cảnh báo")
                self.add_log(current_time.toString("HH:mm:ss"), drive_time, "⏭️ Bỏ qua (timeout)")

            else:
                # User chủ động TỪ CHỐI
                print("❌ User từ chối: TỈNH TÁAO")
                self.add_log(current_time.toString("HH:mm:ss"), drive_time, "❌ Từ chối - Tỉnh táo")

                if self.detector:
                    try:
                        self.detector.update_alert_confirmation(
                            dialog.current_id,
                            confirmed=False,
                        )
                    except:
                        pass

    def show_rest_alert(self):
        dialog = RestAlertDialog(self)
        result = dialog.exec_()
        current_time = QDateTime.currentDateTime()
        drive_time = self.drive_time_label.text().replace("⏱️ ", "")

        if result == RestAlertDialog.Accepted:
            self.add_log(current_time.toString("HH:mm:ss"), drive_time, "🛑 NGHỈ NGƠI")
            self.stop_monitoring()
        else:
            self.add_log(current_time.toString("HH:mm:ss"), drive_time, "⚠️ BỎ QUA")
        self.drowsiness_count = 0
        self.update_alert_count()

    def update_alert_count(self):
        self.alert_count_label.setText(f"⚠️ {self.drowsiness_count}/3")
        if self.drowsiness_count == 0:
            self.alert_count_label.setStyleSheet("color: #27ae60;")
        elif self.drowsiness_count == 1:
            self.alert_count_label.setStyleSheet("color: #f39c12;")
        elif self.drowsiness_count == 2:
            self.alert_count_label.setStyleSheet("color: #e67e22;")
        else:
            self.alert_count_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def update_drive_time(self):
        if self.start_time:
            elapsed = self.start_time.secsTo(QDateTime.currentDateTime())
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.drive_time_label.setText(f"⏱️ {hours:02d}:{minutes:02d}:{seconds:02d}")

    def add_log(self, time, drive_time, status):
        """Thêm log vào bảng"""
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)

        time_item = QTableWidgetItem(time)
        time_item.setFont(QFont('Arial', 9))
        self.log_table.setItem(row, 0, time_item)

        drive_item = QTableWidgetItem(drive_time)
        drive_item.setFont(QFont('Arial', 9))
        self.log_table.setItem(row, 1, drive_item)

        status_item = QTableWidgetItem(status)
        status_item.setFont(QFont('Arial', 9))

        # Phân loại màu sắc
        if "Xác nhận buồn ngủ" in status or "Buồn ngủ" in status or "✅" in status:
            # Xác nhận buồn ngủ - Cam đậm
            status_item.setForeground(QColor("#e67e22"))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
        elif "Từ chối" in status or "Tỉnh táo" in status or "❌" in status:
            # Từ chối chủ động - Xanh lá
            status_item.setForeground(QColor("#27ae60"))
        elif "Bỏ qua" in status or "⏭️" in status or "timeout" in status.lower():
            # Bỏ qua (timeout) - Xám
            status_item.setForeground(QColor("#95a5a6"))
            font = status_item.font()
            font.setItalic(True)
            status_item.setFont(font)
        elif "NGHỈ" in status or "DỪNG" in status or "🛑" in status:
            # Nghỉ ngơi - Đỏ đậm
            status_item.setForeground(QColor("#e74c3c"))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
        elif "BỎ QUA CẢNH BÁO" in status or "⚠️" in status:
            # Bỏ qua cảnh báo nghỉ - Cam
            status_item.setForeground(QColor("#f39c12"))

        self.log_table.setItem(row, 2, status_item)
        self.log_table.scrollToBottom()

    def load_logs_from_db(self):
        if self.detector is None:
            QMessageBox.warning(self, "Warning", "Please start the system first!")
            return
        try:
            alerts = self.detector.get_latest_alerts(50)
            self.log_table.setRowCount(0)
            for alert in reversed(alerts):
                timestamp, duration, confirmed, drowsy_ratio, confidence_avg, notes = alert
                dt = QDateTime.fromString(timestamp, Qt.ISODate)
                time_str = dt.toString("HH:mm:ss")
                status = f"✅ {drowsy_ratio * 100:.0f}%" if confirmed else f"❌ {drowsy_ratio * 100:.0f}%"
                self.add_log(time_str, f"{duration:.0f}s", status)
            QMessageBox.information(self, "Success", f"Loaded {len(alerts)} records")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")

    def clear_log(self):
        if self.log_table.rowCount() == 0:
            return
        reply = QMessageBox.question(self, 'Confirm', 'Clear all logs?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log_table.setRowCount(0)

    def handle_camera_error(self, error_msg):
        QMessageBox.critical(self, "Camera Error", error_msg)
        self.stop_monitoring()

    def handle_logout(self):
        if self.start_time is not None:
            reply = QMessageBox.question(
                self, 'Confirm', 'System is running. Log out?', QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.stop_monitoring()
        self.log_table.setRowCount(0)
        self.logout_signal.emit()

    def set_database(self, db):
        """Set database"""
        self.db = db

    def show_statistics(self):
        """Hiển thị trang thống kê"""
        self.statistics_signal.emit()

    def show_videos(self):
        """Hiển thị trang xem video"""
        self.videos_signal.emit()
