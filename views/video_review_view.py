from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QSlider, QFrame,
                             QComboBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap, QImage
import cv2
import os
from datetime import datetime
from repository.drowsy_video_repo import get_all_drowsy_videos_by_user, update_user_choice_by_id
from utils.VideoManager import VideoManager


class VideoReviewView(QWidget):
    """View xem lại video"""

    back_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.drowsy_videos = []

        # Video playback
        self.video_capture = None
        self.is_playing = False
        self.current_video_path = None
        self.current_fps = 30
        self.playback_speed = 1.0
        self.total_frames = 0
        self.current_frame = 0

        # Timer for video playback
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_frame)

        # video manager
        self.video_manager = VideoManager()

        self.init_ui()

    def init_ui(self):
        """Khởi tạo giao diện"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # Content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Bên trái: Video player
        video_widget = self.create_video_player()
        content_layout.addWidget(video_widget, 60)

        # Bên phải: Video list
        list_widget = self.create_video_list()
        content_layout.addWidget(list_widget, 40)

        main_layout.addLayout(content_layout, 1)

        self.setLayout(main_layout)

    def create_header(self):
        """Tạo header"""
        layout = QHBoxLayout()

        # Title
        title_label = QLabel("🎬 XEM LẠI VIDEO CẢNH BÁO")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        # Filter
        filter_label = QLabel("Lọc:")
        filter_label.setFont(QFont('Arial', 9))

        self.status_filter = QComboBox()
        self.status_filter.addItems(['Tất cả', 'Chưa xác nhận', 'Đã xác nhận', 'Từ chối'])
        self.status_filter.setMinimumWidth(120)
        self.status_filter.setMaximumHeight(30)
        self.status_filter.setStyleSheet("""
            QComboBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
                font-size: 9px;
            }
        """)
        self.status_filter.currentIndexChanged.connect(self.filter_videos)

        # Back button
        back_button = QPushButton("← Quay lại")
        back_button.setMaximumHeight(30)
        back_button.setMinimumWidth(100)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        back_button.clicked.connect(self.back_signal.emit)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(filter_label)
        layout.addWidget(self.status_filter)
        layout.addWidget(back_button)

        return layout

    def create_video_player(self):
        """Tạo video player"""
        group = QGroupBox("📹 Video Player")
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
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Video display
        self.video_frame = QLabel()
        self.video_frame.setMinimumSize(480, 360)
        self.video_frame.setMaximumSize(640, 480)
        self.video_frame.setAlignment(Qt.AlignCenter)
        self.video_frame.setScaledContents(True)  # Scale to fit
        self.video_frame.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 5px;
                color: white;
                font-size: 12px;
            }
        """)
        self.video_frame.setText("📹\n\nChọn video từ danh sách")

        # Video info
        info_layout = QHBoxLayout()

        self.video_title_label = QLabel("Chưa chọn video")
        self.video_title_label.setFont(QFont('Arial', 9, QFont.Bold))

        self.video_time_label = QLabel("00:00 / 00:00")
        self.video_time_label.setFont(QFont('Arial', 8))
        self.video_time_label.setStyleSheet("color: #7f8c8d;")

        info_layout.addWidget(self.video_title_label)
        info_layout.addStretch()
        info_layout.addWidget(self.video_time_label)

        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.setMaximumHeight(20)
        self.progress_slider.sliderMoved.connect(self.seek_video)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)

        # Controls
        controls_layout = QHBoxLayout()

        self.play_button = QPushButton("▶️ Phát")
        self.play_button.setMaximumHeight(30)
        self.play_button.setEnabled(False)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover:enabled {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.play_button.clicked.connect(self.toggle_playback)

        speed_label = QLabel("Tốc độ:")
        speed_label.setFont(QFont('Arial', 8))

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(['0.5x', '1x', '1.5x', '2x'])
        self.speed_combo.setCurrentText('1x')
        self.speed_combo.setMaximumWidth(60)
        self.speed_combo.setMaximumHeight(25)
        self.speed_combo.currentTextChanged.connect(self.change_speed)

        controls_layout.addWidget(self.play_button)
        controls_layout.addStretch()
        controls_layout.addWidget(speed_label)
        controls_layout.addWidget(self.speed_combo)

        # Review section
        review_group = QFrame()
        review_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        review_layout = QVBoxLayout(review_group)
        review_layout.setSpacing(5)

        review_title = QLabel("✍️ Xác nhận thủ công")
        review_title.setFont(QFont('Arial', 9, QFont.Bold))

        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Trạng thái:"))

        self.review_status = QComboBox()
        self.review_status.addItems(['Chưa xác nhận', 'Xác nhận buồn ngủ',
                                     'Từ chối - Tỉnh táo', 'False Positive'])
        self.review_status.setMinimumWidth(150)
        self.review_status.setMaximumHeight(25)

        status_layout.addWidget(self.review_status)
        status_layout.addStretch()

        # # Notes
        # notes_label = QLabel("Ghi chú:")
        # notes_label.setFont(QFont('Arial', 8))
        #
        # self.notes_text = QTextEdit()
        # self.notes_text.setMaximumHeight(50)
        # self.notes_text.setPlaceholderText("Nhập ghi chú...")
        # self.notes_text.setStyleSheet("""
        #     QTextEdit {
        #         border: 1px solid #bdc3c7;
        #         border-radius: 3px;
        #         padding: 5px;
        #         font-size: 8px;
        #     }
        # """)

        # Save button
        save_button = QPushButton("💾 Lưu xác nhận")
        save_button.setMaximumHeight(30)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_button.clicked.connect(self.save_review)

        review_layout.addWidget(review_title)
        review_layout.addLayout(status_layout)
        # review_layout.addWidget(notes_label)
        # review_layout.addWidget(self.notes_text)
        review_layout.addWidget(save_button)

        # Add to main layout
        layout.addWidget(self.video_frame)
        layout.addLayout(info_layout)
        layout.addWidget(self.progress_slider)
        layout.addLayout(controls_layout)
        layout.addWidget(review_group)

        group.setLayout(layout)
        return group

    def create_video_list(self):
        """Tạo danh sách video"""
        group = QGroupBox("📋 Danh sách video")
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
            }
        """)

        layout = QVBoxLayout()

        # Table
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(3)
        self.video_table.setHorizontalHeaderLabels(['Thời điểm bắt đầu', "Thời điểm kết thúc", 'Trạng thái'])

        self.video_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                gridline-color: #ecf0f1;
                font-size: 8px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
                font-size: 8px;
            }
        """)

        self.video_table.verticalHeader().setDefaultSectionSize(28)
        self.video_table.verticalHeader().setVisible(False)
        self.video_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.video_table.setSelectionMode(QTableWidget.SingleSelection)

        header = self.video_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.video_table.itemSelectionChanged.connect(self.on_video_selected)

        # Stats
        self.stats_label = QLabel("Tổng: 0 video")
        self.stats_label.setFont(QFont('Arial', 8))
        self.stats_label.setStyleSheet("color: #7f8c8d;")

        layout.addWidget(self.video_table)
        layout.addWidget(self.stats_label)

        group.setLayout(layout)
        return group

    def load_videos(self):
        """Tải danh sách video từ database"""
        try:
            self.video_table.setRowCount(0)
            self.drowsy_videos = []

            user_id = self.current_user['id'] if self.current_user else 0
            data_videos = get_all_drowsy_videos_by_user(user_id=user_id)

            for video in data_videos:
                video_data = {
                    'id': video['id'],
                    'start_time': datetime.fromisoformat(video['start_time']),
                    'end_time': datetime.fromisoformat(video['end_time']),
                    'video_path': self.video_manager.get_drowsy_video(video['id']),
                    # 'video_path': "",
                    'status': ('Từ chối - Tỉnh táo' if video['userChoiceLabel'] == 0 else
                               'Đã xác nhận' if video['userChoiceLabel'] == 1 else 'Chưa xác nhận')
                }
                self.drowsy_videos.append(video_data)
                self.add_video_to_table(video_data)

            self.stats_label.setText(f"Tổng: {len(self.drowsy_videos)} video")
        except Exception as e:
            print(f"⚠️ Lỗi load videos: {e}")
            import traceback
            traceback.print_exc()

    def add_video_to_table(self, video_data):
        """Thêm video vào bảng"""
        try:
            row = self.video_table.rowCount()
            self.video_table.insertRow(row)

            # Start Time
            start_time_str = video_data['start_time'].strftime('%d/%m %H:%M:%S')
            start_time_item = QTableWidgetItem(start_time_str)
            start_time_item.setFont(QFont('Arial', 8))
            self.video_table.setItem(row, 0, start_time_item)

            # End Time
            end_time_str = video_data['end_time'].strftime('%d/%m %H:%M:%S')
            end_time_item = QTableWidgetItem(end_time_str)
            end_time_item.setFont(QFont('Arial', 8))
            self.video_table.setItem(row, 1, end_time_item)

            # Status
            status_short = video_data['status'].split('-')[0].strip()
            status_item = QTableWidgetItem(status_short)
            status_item.setFont(QFont('Arial', 8))
            if 'Chưa' in video_data['status']:
                status_item.setForeground(QColor("#95a5a6"))
            elif 'Đã xác nhận' in video_data['status']:
                status_item.setForeground(QColor("#e74c3c"))
            else:
                status_item.setForeground(QColor("#27ae60"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.video_table.setItem(row, 2, status_item)
        except Exception as e:
            print(f"⚠️ Lỗi add video to table: {e}")

    def on_video_selected(self):
        """Khi chọn video"""
        try:
            # Dừng video hiện tại nếu đang phát
            if self.is_playing:
                self.stop_playback()

            selected_rows = self.video_table.selectedItems()
            if not selected_rows:
                return

            row = selected_rows[0].row()
            if row < len(self.drowsy_videos):
                video_data = self.drowsy_videos[row]

                # Lấy đường dẫn video
                video_path = video_data.get('video_path', '')

                # Update UI
                time_diff = video_data["end_time"] - video_data["start_time"]
                self.video_title_label.setText(
                    f"Video #{video_data['id']} - {video_data['start_time'].strftime('%d/%m/%Y %H:%M:%S')}")
                self.video_time_label.setText(f"00:00 / {time_diff.seconds // 60:02d}:{time_diff.seconds % 60:02d}")

                # Load video nếu có đường dẫn
                if video_path and os.path.exists(video_path):
                    self.load_video(video_path)
                    self.play_button.setEnabled(True)
                    print(f"✅ Đã load video: {video_path}")
                else:
                    # Hiển thị placeholder nếu không có video
                    self.video_frame.setScaledContents(False)
                    self.video_frame.setText(
                        f"🎬\n\nVideo #{video_data['id']}\n"
                        f"{video_data['start_time'].strftime('%d/%m/%Y %H:%M')}\n\n"
                        f"⚠️ File video không tồn tại\n{video_path}"
                    )
                    self.play_button.setEnabled(False)
                    print(f"⚠️ File không tồn tại: {video_path}")

                # Update review status
                if 'Chưa' in video_data['status']:
                    self.review_status.setCurrentIndex(0)
                elif 'Xác nhận' in video_data['status']:
                    self.review_status.setCurrentIndex(1)
                else:
                    self.review_status.setCurrentIndex(2)

                # self.notes_text.clear()
        except Exception as e:
            print(f"⚠️ Lỗi select video: {e}")
            import traceback
            traceback.print_exc()

    def load_video(self, video_path):
        """Load video file"""
        try:
            # Release video cũ nếu có
            if self.video_capture is not None:
                self.video_capture.release()

            # Mở video mới
            self.video_capture = cv2.VideoCapture(video_path)

            if not self.video_capture.isOpened():
                raise Exception(f"Không thể mở video: {video_path}")

            # Lấy thông tin video
            self.current_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            if self.current_fps == 0:
                self.current_fps = 30  # Default FPS

            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_frame = 0
            self.current_video_path = video_path

            # Hiển thị frame đầu tiên
            self.show_frame(0)

            # Reset slider
            self.progress_slider.setValue(0)

            print(f"✅ Video loaded: FPS={self.current_fps}, Total frames={self.total_frames}")

        except Exception as e:
            print(f"⚠️ Lỗi load video: {e}")
            QMessageBox.warning(self, "Lỗi", f"Không thể load video:\n{str(e)}")
            self.play_button.setEnabled(False)

    def show_frame(self, frame_number):
        """Hiển thị một frame cụ thể"""
        try:
            if self.video_capture is None:
                return

            # Set vị trí frame
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.video_capture.read()

            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to QImage
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # Convert to QPixmap and display
                pixmap = QPixmap.fromImage(qt_image)
                self.video_frame.setScaledContents(True)
                self.video_frame.setPixmap(pixmap)

                self.current_frame = frame_number

                # Update time label
                current_time = frame_number / self.current_fps
                total_time = self.total_frames / self.current_fps
                self.video_time_label.setText(
                    f"{int(current_time // 60):02d}:{int(current_time % 60):02d} / "
                    f"{int(total_time // 60):02d}:{int(total_time % 60):02d}"
                )

                # Update slider
                if self.total_frames > 0:
                    progress = int((frame_number / self.total_frames) * 100)
                    self.progress_slider.blockSignals(True)
                    self.progress_slider.setValue(progress)
                    self.progress_slider.blockSignals(False)

        except Exception as e:
            print(f"⚠️ Lỗi show frame: {e}")

    def toggle_playback(self):
        """Bật/tắt phát video"""
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """Bắt đầu phát video"""
        if self.video_capture is None:
            return

        self.is_playing = True
        self.play_button.setText("⏸️ Tạm dừng")
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)

        # Tính interval dựa trên FPS và speed
        interval = int(1000 / (self.current_fps * self.playback_speed))
        self.video_timer.start(interval)

        print(f"▶️ Phát video: FPS={self.current_fps}, Speed={self.playback_speed}x, Interval={interval}ms")

    def pause_playback(self):
        """Tạm dừng phát video"""
        self.is_playing = False
        self.video_timer.stop()
        self.play_button.setText("▶️ Phát")
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        print("⏸️ Tạm dừng video")

    def stop_playback(self):
        """Dừng phát video"""
        self.is_playing = False
        self.video_timer.stop()
        self.current_frame = 0
        if self.video_capture:
            self.show_frame(0)

    def update_frame(self):
        """Cập nhật frame tiếp theo"""
        try:
            if not self.is_playing or self.video_capture is None:
                return

            # Đọc frame tiếp theo
            ret, frame = self.video_capture.read()

            if ret:
                # Convert và hiển thị
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                self.video_frame.setPixmap(pixmap)

                # Update current frame
                self.current_frame = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES))

                # Update time
                current_time = self.current_frame / self.current_fps
                total_time = self.total_frames / self.current_fps
                self.video_time_label.setText(
                    f"{int(current_time // 60):02d}:{int(current_time % 60):02d} / "
                    f"{int(total_time // 60):02d}:{int(total_time % 60):02d}"
                )

                # Update slider
                if self.total_frames > 0:
                    progress = int((self.current_frame / self.total_frames) * 100)
                    self.progress_slider.blockSignals(True)
                    self.progress_slider.setValue(progress)
                    self.progress_slider.blockSignals(False)
            else:
                # Hết video - quay về đầu
                print("🔚 Video đã kết thúc")
                self.pause_playback()
                self.show_frame(0)

        except Exception as e:
            print(f"⚠️ Lỗi update frame: {e}")
            self.pause_playback()

    def seek_video(self, value):
        """Tua video đến vị trí cụ thể"""
        try:
            if self.video_capture is None or self.total_frames == 0:
                return

            # Tính frame number từ slider value
            frame_number = int((value / 100) * self.total_frames)
            self.show_frame(frame_number)

        except Exception as e:
            print(f"⚠️ Lỗi seek video: {e}")

    def on_slider_pressed(self):
        """Khi bắt đầu kéo slider"""
        self.was_playing = self.is_playing
        if self.is_playing:
            self.pause_playback()

    def on_slider_released(self):
        """Khi thả slider"""
        if self.was_playing:
            self.start_playback()

    def change_speed(self, speed_text):
        """Thay đổi tốc độ phát"""
        try:
            # Parse speed value
            self.playback_speed = float(speed_text.replace('x', ''))

            # Update timer interval nếu đang phát
            if self.is_playing:
                self.pause_playback()
                self.start_playback()

            print(f"⚡ Tốc độ: {self.playback_speed}x")

        except Exception as e:
            print(f"⚠️ Lỗi change speed: {e}")

    def save_review(self):
        """Lưu xác nhận"""
        try:
            selected_rows = self.video_table.selectedItems()
            if not selected_rows:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn video!")
                return

            status = self.review_status.currentText()

            row = selected_rows[0].row()
            status_item = self.video_table.item(row, 2)
            status_short = status.split('-')[0].strip()
            status_item.setText(status_short)
            st = ""
            if 'Chưa' in status:
                st = None
                status_item.setForeground(QColor("#95a5a6"))
            elif 'Xác nhận' in status:
                st = True
                status_item.setForeground(QColor("#e74c3c"))
            elif 'Từ chối' in status:
                st = False
                status_item.setForeground(QColor("#27ae60"))

            # TODO: Lưu vào database
            video_id = self.drowsy_videos[row]['id']
            update_user_choice_by_id(id=video_id, user_choice=st)
            QMessageBox.information(self, "Thành công", f"Đã lưu!\n\n{status}")
        except Exception as e:
            print(f"⚠️ Lỗi save review: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu:\n{str(e)}")

    def filter_videos(self):
        """Lọc video"""
        try:
            filter_text = self.status_filter.currentText()

            for row in range(self.video_table.rowCount()):
                status_item = self.video_table.item(row, 2)
                print(status_item.text())
                if status_item:
                    if filter_text == 'Tất cả':
                        self.video_table.setRowHidden(row, False)
                    else:
                        should_hide = filter_text.split()[0] not in status_item.text()
                        self.video_table.setRowHidden(row, should_hide)
        except Exception as e:
            print(f"⚠️ Lỗi filter: {e}")

    def set_user_info(self, user_info):
        """Set user và load data"""
        try:
            self.current_user = user_info
            self.load_videos()
        except Exception as e:
            print(f"⚠️ Lỗi set user: {e}")

    def cleanup(self):
        """Dọn dẹp resources khi đóng view"""
        try:
            if self.is_playing:
                self.pause_playback()
            if self.video_capture is not None:
                self.video_capture.release()
                self.video_capture = None
            print("✅ Đã cleanup video resources")
        except Exception as e:
            print(f"⚠️ Lỗi cleanup: {e}")
