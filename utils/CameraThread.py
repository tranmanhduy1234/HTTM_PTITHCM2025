from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np


class CameraThread(QThread):
    """Thread xử lý camera và phát hiện buồn ngủ"""

    # Signals
    frame_ready = pyqtSignal(QPixmap, dict)  # (frame, status_dict)
    drowsiness_alert = pyqtSignal(float, float)  # (drowsy_ratio, confidence)
    error_occurred = pyqtSignal(str)

    def __init__(self, detector, camera_source=0):
        super().__init__()
        self.detector = detector
        self.camera_source = camera_source
        self.running = False
        self.cap = None

        # Set callback cho detector
        self.detector.callback = self._on_drowsiness_detected

    def _on_drowsiness_detected(self, frame, drowsy_ratio, confidence):
        """Callback khi phát hiện buồn ngủ"""
        self.drowsiness_alert.emit(drowsy_ratio, confidence)

    def run(self):
        """Chạy thread"""
        self.running = True
        self.cap = cv2.VideoCapture(self.camera_source)

        # Cấu hình camera
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        if not self.cap.isOpened():
            self.error_occurred.emit("Không thể mở camera!")
            return

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.error_occurred.emit("Không đọc được frame từ camera!")
                break

            # Xử lý frame qua detector
            processed_frame, status = self.detector.process_frame(frame)

            # Convert sang QPixmap
            pixmap = self._convert_cv_to_pixmap(processed_frame)

            # Emit signal
            self.frame_ready.emit(pixmap, status)

            # Giảm tải CPU
            self.msleep(33)  # ~30 FPS

        self._cleanup()

    def _convert_cv_to_pixmap(self, cv_img):
        """Convert OpenCV image sang QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_image)

    def stop(self):
        """Dừng thread"""
        self.running = False
        self.wait(3000)  # Đợi tối đa 3 giây

    def _cleanup(self):
        """Dọn dẹp resources"""
        if self.cap is not None:
            self.cap.release()
