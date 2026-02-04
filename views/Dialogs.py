# dialogs.py - Tích hợp Audio Detection

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from utils.sound_manager import get_sound_manager

import pyaudio
import torch
import numpy as np
from queue import Queue
from threading import Event
import torch.nn.functional as F
import time

# ==================== AUDIO DETECTION COMPONENTS ====================

# Try to import model components
AUDIO_DETECTION_AVAILABLE = False
try:
    from core.model_conformer import ConformerClassifier
    from core.Util import audio2inputmodel

    AUDIO_DETECTION_AVAILABLE = True
except ImportError:
    print("⚠️ Audio detection model not available - running without voice control")

# Global model instance (loaded once)
_audio_model = None
_audio_model_loaded = False


def get_audio_model():
    """Get or load the audio detection model (singleton)"""
    global _audio_model, _audio_model_loaded

    if _audio_model_loaded:
        return _audio_model

    if not AUDIO_DETECTION_AVAILABLE:
        _audio_model_loaded = True
        return None

    try:
        _audio_model = torch.nn.DataParallel(ConformerClassifier())
        _audio_model.load_state_dict(torch.load(
            r"core/lastest_2025-12-25_20-43-56.pt",
            map_location="cuda"
        ))
        _audio_model = _audio_model.to("cuda").eval()
        _audio_model_loaded = True
        print("✓ Audio detection model loaded successfully")
    except Exception as e:
        print(f"⚠️ Cannot load audio model: {e}")
        _audio_model = None
        _audio_model_loaded = True

    return _audio_model


class AudioDetectionWorker(QThread):
    """
    Qt Worker for audio detection - runs in background thread

    Signals:
        detection_result: Emits True (label=1, drowsy), False (label=0, alert), or None (timeout/error)
        prediction_update: Emits (label, confidence, elapsed_time) for UI updates
    """
    detection_result = pyqtSignal(object)
    prediction_update = pyqtSignal(int, float, float)

    def __init__(self, model, sample_rate=44100, chunk_size=1024,
                 device_index=None, timeout=20, chunk_duration=2.0, overlap=0.75):
        super().__init__()
        self.model = model
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.timeout = timeout
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.hop_samples = int(self.chunk_samples * (1 - overlap))
        self.min_prediction_interval = chunk_duration * (1 - overlap)

        self.is_running = Event()
        self._stopped_externally = False

    def run(self):
        """Main detection loop"""
        if self.model is None:
            self.detection_result.emit(None)
            return

        self.is_running.set()
        self._stopped_externally = False

        p = None
        stream = None

        try:
            # Setup audio
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            print("🎤 Bắt đầu phát hiện âm thanh...")
        except Exception as e:
            print(f"⚠️ Cannot open audio stream: {e}")
            self.detection_result.emit(None)
            return

        buffer = []
        last_prediction_time = time.time()
        last_prediction_label = -1
        start_time = time.time()
        result = None

        try:
            while self.is_running.is_set():
                # Read audio
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    buffer.extend(audio_data)
                except Exception as e:
                    continue

                current_time = time.time()
                elapsed = current_time - start_time

                # Check timeout
                if elapsed >= self.timeout:
                    print(f"⏱️ Audio detection timeout ({self.timeout}s)")
                    result = None  # Timeout = no definitive result
                    break

                # Make prediction if we have enough samples
                if (len(buffer) >= self.chunk_samples and
                        current_time - last_prediction_time >= self.min_prediction_interval):

                    chunk = np.array(buffer[:self.chunk_samples])

                    try:
                        label, confidence = self._process_chunk(chunk)

                        self.prediction_update.emit(label, confidence, elapsed)
                        last_prediction_time = current_time

                        print(f"[{elapsed:.1f}s] Audio prediction: label={label}, confidence={confidence:.4f}")

                        if label == 1:  # Buồn ngủ
                            if last_prediction_label == 1:
                                result = True  # 2 consecutive "drowsy" = confirm drowsy
                                print("✓ Phát hiện 2 lần liên tiếp: BUỒN NGỦ")
                                break
                            last_prediction_label = 1
                        # elif label == 0:  # Tỉnh táo
                        #     if last_prediction_label == 0:
                        #         result = False  # 2 consecutive "alert" = confirm alert
                        #         print("✓ Phát hiện 2 lần liên tiếp: TỈNH TÁO")
                        #         break
                        #     last_prediction_label = 0
                        else:
                            # Các label khác (2, 3, ...) không xử lý, reset
                            last_prediction_label = -1

                    except Exception as e:
                        print(f"Prediction error: {e}")

                    # Shift buffer
                    buffer = buffer[self.hop_samples:]

        except Exception as e:
            print(f"Audio detection error: {e}")
            result = None
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            if p:
                p.terminate()
            print("🎤 Dừng phát hiện âm thanh")

        # Only emit result if not stopped externally
        if not self._stopped_externally:
            self.detection_result.emit(result)

    def _process_chunk(self, audio_chunk):
        """Process audio chunk and return prediction"""
        waveform = torch.FloatTensor(audio_chunk).unsqueeze(0)
        aud = audio2inputmodel((waveform, self.sample_rate)).to("cuda")

        with torch.no_grad():
            output, _ = self.model(aud)
            probabilities = F.softmax(output, dim=-1)
            prob = torch.max(probabilities, dim=-1)
            confidence = prob.values.item()
            label = prob.indices.item()

        return label, confidence

    def stop(self):
        """Stop detection"""
        self._stopped_externally = True
        self.is_running.clear()


# ==================== DIALOG CLASSES ====================

class DrowsinessAlertDialog(QDialog):
    """Dialog cảnh báo buồn ngủ

    Tích hợp audio detection:
    - Audio label 1 (2 lần liên tiếp) → accept (xác nhận buồn ngủ)
    - Audio label 0 (2 lần liên tiếp) → reject (tỉnh táo)
    - Audio timeout → đánh dấu is_timeout = True và reject
    """

    def __init__(self, parent=None, current_id=None, enable_audio_detection=True):
        super().__init__(parent)
        # info
        self.current_id = current_id
        self.setWindowTitle("⚠️ CẢNH BÁO BUỒN NGỦ")
        self.setModal(True)
        self.setFixedSize(500, 380)

        # Sound manager
        self.sound_manager = None
        self.sound_started = False

        # Countdown timer
        self.remaining_seconds = 9  # s

        # Flag để phân biệt timeout vs user action
        self.is_timeout = False

        # Audio detection
        self.enable_audio_detection = enable_audio_detection and AUDIO_DETECTION_AVAILABLE
        self.audio_worker = None
        self.audio_result_received = False

        self.init_ui()

        # Phát âm thanh sau khi UI đã sẵn sàng
        QTimer.singleShot(100, self.start_sound)

        # Bắt đầu audio detection
        if self.enable_audio_detection:
            QTimer.singleShot(200, self.start_audio_detection)

        # Auto close sau 30 giây
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.auto_reject)
        self.auto_close_timer.start(self.remaining_seconds * 1000)

        # Countdown timer (cập nhật mỗi giây)
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

    def start_audio_detection(self):
        """Bắt đầu audio detection"""
        model = get_audio_model()
        if model is None:
            print("⚠️ Audio model not available, using button-only mode")
            self.audio_status_label.setText("🔇 Điều khiển giọng nói không khả dụng")
            self.audio_status_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-style: italic;
                    background-color: #e9ecef;
                    padding: 5px;
                    border-radius: 3px;
                }
            """)
            return

        self.audio_worker = AudioDetectionWorker(
            model=model,
            timeout=30,  # Timeout ngắn hơn dialog timeout
            chunk_duration=2.0,
            overlap=0.75
        )
        self.audio_worker.detection_result.connect(self.on_audio_result)
        self.audio_worker.prediction_update.connect(self.on_audio_prediction)
        self.audio_worker.start()

        self.audio_status_label.setText("🎤 Đang lắng nghe phản hồi bằng giọng nói...")

    def on_audio_result(self, result):
        """Xử lý kết quả từ audio detection"""
        if self.audio_result_received:
            return

        self.audio_result_received = True

        if result is True:
            # Audio detected drowsy (label 1, 2 consecutive) → ACCEPT
            print("🎤 Audio: Phát hiện XÁC NHẬN buồn ngủ → Đóng dialog")
            self.is_timeout = False
            self.accept_and_stop_sound()

        # elif result is False:
        #     # Audio detected alert (label 0, 2 consecutive) → REJECT
        #     print("🎤 Audio: Phát hiện TỈNH TÁO → Đóng dialog")
        #     self.is_timeout = False
        #     self.reject_and_stop_sound()

        else:
            # Audio timeout → đánh dấu timeout và reject
            print("🎤 Audio: Timeout - Không phát hiện được xác nhận → Ghi nhận TIMEOUT")
            self.audio_status_label.setText("⏱️ TIMEOUT - Không nhận được phản hồi giọng nói")
            self.audio_status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    background-color: #f8d7da;
                    padding: 5px;
                    border-radius: 3px;
                    border: 1px solid #e74c3c;
                }
            """)
            self.is_timeout = True  # Đánh dấu là TIMEOUT
            self.stop_sound()
            self.stop_audio_detection()
            self.reject()

    def on_audio_prediction(self, label, confidence, elapsed):
        """Cập nhật UI khi có prediction mới"""
        if label == 1:
            label_text = "Buồn ngủ"
            color = "#e74c3c"
        elif label == 0:
            label_text = "Tỉnh táo"
            color = "#27ae60"
        else:
            label_text = f"Khác ({label})"
            color = "#6c757d"

        self.audio_status_label.setText(
            f"🎤 [{elapsed:.1f}s] Đang phân tích: {label_text} ({confidence:.1%})"
        )
        self.audio_status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: bold;
                background-color: #e3f2fd;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #90caf9;
            }}
        """)

    def start_sound(self):
        """Bắt đầu phát âm thanh"""
        try:
            self.sound_manager = get_sound_manager()
            self.sound_manager.play_alert(loop=True)
            self.sound_started = True
        except Exception as e:
            print(f"⚠️ Không thể phát âm thanh: {e}")

    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Warning icon
        warning_label = QLabel("⚠️")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("font-size: 70px;")

        # Title
        title_label = QLabel("PHÁT HIỆN DẤU HIỆU BUỒN NGỦ!")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        title_label.setStyleSheet("color: #e67e22;")

        # Message
        message_label = QLabel("Bạn có đang buồn ngủ không?")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setFont(QFont('Arial', 13))
        message_label.setStyleSheet("color: #2c3e50;")

        # Audio status label
        self.audio_status_label = QLabel("🎤 Đang khởi tạo nhận diện giọng nói...")
        self.audio_status_label.setAlignment(Qt.AlignCenter)
        self.audio_status_label.setFont(QFont('Arial', 10))
        self.audio_status_label.setStyleSheet("""
            QLabel {
                color: #0066cc;
                font-style: italic;
                background-color: #e3f2fd;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #90caf9;
            }
        """)

        # Countdown label
        self.countdown_label = QLabel(f"⏱️ Tự động đóng sau: {self.remaining_seconds}s")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setFont(QFont('Arial', 10))
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: #e67e22;
                background-color: #fff3cd;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #ffc107;
            }
        """)

        # Timeout warning
        self.timeout_warning = QLabel("⚠️ Nếu không phản hồi → Ghi nhận là TIMEOUT")
        self.timeout_warning.setAlignment(Qt.AlignCenter)
        self.timeout_warning.setFont(QFont('Arial', 9))
        self.timeout_warning.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-style: italic;
                background-color: #f8d7da;
                padding: 3px;
                border-radius: 3px;
            }
        """)

        # Sound indicator
        self.sound_label = QLabel("🔊 Âm thanh cảnh báo đang phát...")
        self.sound_label.setAlignment(Qt.AlignCenter)
        self.sound_label.setFont(QFont('Arial', 9))
        self.sound_label.setStyleSheet("""
            QLabel {
                color: #e67e22;
                font-style: italic;
                background-color: #fff3cd;
                padding: 5px;
                border-radius: 3px;
            }
        """)

        # Buttons
        button_layout = QHBoxLayout()

        yes_button = QPushButton("Có, tôi buồn ngủ")
        yes_button.setMinimumHeight(45)
        yes_button.setFont(QFont('Arial', 11, QFont.Bold))
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        yes_button.clicked.connect(self.accept_and_stop_sound)

        no_button = QPushButton("Không, tôi tỉnh táo")
        no_button.setMinimumHeight(45)
        no_button.setFont(QFont('Arial', 11, QFont.Bold))
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        no_button.clicked.connect(self.reject_and_stop_sound)

        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)

        # Add to main layout
        layout.addWidget(warning_label)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addWidget(self.audio_status_label)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.timeout_warning)
        layout.addWidget(self.sound_label)
        layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Style dialog
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 3px solid #e67e22;
                border-radius: 10px;
            }
        """)

        # Blinking effect
        self.blink_timer = QTimer()
        self.blink_state = True
        self.blink_timer.timeout.connect(self.blink_labels)
        self.blink_timer.start(500)

    def update_countdown(self):
        """Cập nhật countdown"""
        self.remaining_seconds -= 1
        self.countdown_label.setText(f"⏱️ Tự động đóng sau: {self.remaining_seconds}s")

        # Đổi màu khi sắp hết thời gian
        if self.remaining_seconds <= 10:
            self.countdown_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    background-color: #f8d7da;
                    padding: 5px;
                    border-radius: 3px;
                    border: 1px solid #e74c3c;
                    font-weight: bold;
                }
            """)

            # Blink warning nhanh hơn
            if self.remaining_seconds <= 5:
                self.blink_timer.setInterval(300)

    def blink_labels(self):
        """Nhấp nháy các label"""
        if self.blink_state:
            self.sound_label.setStyleSheet("""
                QLabel {
                    color: #e67e22;
                    font-style: italic;
                    background-color: #fff3cd;
                    padding: 5px;
                    border-radius: 3px;
                }
            """)
            if self.remaining_seconds <= 10:
                self.timeout_warning.setStyleSheet("""
                    QLabel {
                        color: #e74c3c;
                        font-style: italic;
                        background-color: #f8d7da;
                        padding: 3px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                """)
        else:
            self.sound_label.setStyleSheet("""
                QLabel {
                    color: #c0392b;
                    font-style: italic;
                    background-color: #f8d7da;
                    padding: 5px;
                    border-radius: 3px;
                }
            """)
            if self.remaining_seconds <= 10:
                self.timeout_warning.setStyleSheet("""
                    QLabel {
                        color: #c0392b;
                        font-style: italic;
                        background-color: #fadbd8;
                        padding: 3px;
                        border-radius: 3px;
                    }
                """)
        self.blink_state = not self.blink_state

    def accept_and_stop_sound(self):
        """Xác nhận và dừng âm thanh"""
        self.is_timeout = False  # User chủ động xác nhận
        self.stop_sound()
        self.stop_audio_detection()
        self.accept()

    def reject_and_stop_sound(self):
        """Từ chối và dừng âm thanh"""
        self.is_timeout = False  # User chủ động từ chối
        self.stop_sound()
        self.stop_audio_detection()
        self.reject()

    def auto_reject(self):
        """Tự động từ chối khi dialog timeout"""
        print("⏱️ Dialog Timeout - Tự động ghi nhận là TIMEOUT")
        self.is_timeout = True  # Đánh dấu là timeout
        self.stop_sound()
        self.stop_audio_detection()
        self.reject()

    def stop_sound(self):
        """Dừng âm thanh"""
        try:
            if self.sound_manager and self.sound_started:
                self.sound_manager.stop_alert()
                self.sound_started = False
        except Exception as e:
            print(f"⚠️ Lỗi dừng âm thanh: {e}")

        try:
            self.auto_close_timer.stop()
            self.countdown_timer.stop()
            self.blink_timer.stop()
        except:
            pass

    def stop_audio_detection(self):
        """Dừng audio detection"""
        if self.audio_worker and self.audio_worker.isRunning():
            self.audio_worker.stop()
            self.audio_worker.wait(1000)  # Wait up to 1 second

    def closeEvent(self, event):
        """Xử lý khi đóng dialog"""
        self.stop_sound()
        self.stop_audio_detection()
        event.accept()


class RestAlertDialog(QDialog):
    """Dialog cảnh báo nghỉ ngơi

    Tích hợp audio detection:
    - Audio label 1 (2 lần liên tiếp) → accept (dừng lại nghỉ ngơi)
    - Audio label 0 (2 lần liên tiếp) → reject (tiếp tục - nguy hiểm)
    - Audio timeout → đánh dấu is_timeout = True và reject
    """

    def __init__(self, parent=None, enable_audio_detection=True):
        super().__init__(parent)
        self.setWindowTitle("🚨 CẢNH BÁO NGHIÊM TRỌNG")
        self.setModal(True)
        self.setFixedSize(550, 450)

        # Sound manager
        self.sound_manager = None
        self.sound_started = False

        # Flag để phân biệt timeout vs user action
        self.is_timeout = False

        # Audio detection
        self.enable_audio_detection = enable_audio_detection and AUDIO_DETECTION_AVAILABLE
        self.audio_worker = None
        self.audio_result_received = False

        self.init_ui()

        # Phát âm thanh sau khi UI sẵn sàng
        QTimer.singleShot(100, self.start_sound)

        # Bắt đầu audio detection
        if self.enable_audio_detection:
            QTimer.singleShot(200, self.start_audio_detection)

    def start_audio_detection(self):
        """Bắt đầu audio detection"""
        model = get_audio_model()
        if model is None:
            print("⚠️ Audio model not available, using button-only mode")
            self.audio_status_label.setText("🔇 Điều khiển giọng nói không khả dụng")
            self.audio_status_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-style: italic;
                    background-color: #e9ecef;
                    padding: 8px;
                    border-radius: 5px;
                }
            """)
            return

        self.audio_worker = AudioDetectionWorker(
            model=model,
            timeout=30,  # Timeout cho rest dialog
            chunk_duration=2.0,
            overlap=0.75
        )
        self.audio_worker.detection_result.connect(self.on_audio_result)
        self.audio_worker.prediction_update.connect(self.on_audio_prediction)
        self.audio_worker.start()

    def on_audio_result(self, result):
        """Xử lý kết quả từ audio detection"""
        if self.audio_result_received:
            return

        self.audio_result_received = True

        if result is True:
            # Audio detected "yes" (label 1) → accept (will rest)
            print("🎤 Audio: Phát hiện XÁC NHẬN nghỉ ngơi → Đóng dialog")
            self.is_timeout = False
            self.accept_and_stop_sound()

        elif result is False:
            # Audio detected "no" (label 0) → reject (will continue - dangerous)
            print("🎤 Audio: Phát hiện TIẾP TỤC lái xe → Đóng dialog")
            self.is_timeout = False
            self.reject_and_stop_sound()

        else:
            # Audio timeout → đánh dấu timeout và reject
            print("🎤 Audio: Timeout - Không phát hiện được xác nhận → Ghi nhận TIMEOUT")
            self.audio_status_label.setText("⏱️ TIMEOUT - Không nhận được phản hồi giọng nói")
            self.audio_status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    background-color: #f8d7da;
                    padding: 8px;
                    border-radius: 5px;
                    border: 1px solid #e74c3c;
                }
            """)
            self.is_timeout = True  # Đánh dấu là TIMEOUT
            self.stop_sound()
            self.stop_audio_detection()
            self.reject()

    def on_audio_prediction(self, label, confidence, elapsed):
        """Cập nhật UI khi có prediction mới"""
        if label == 1:
            label_text = "Đồng ý nghỉ"
            color = "#27ae60"
        elif label == 0:
            label_text = "Tiếp tục"
            color = "#e74c3c"
        else:
            label_text = f"Khác ({label})"
            color = "#6c757d"

        self.audio_status_label.setText(
            f"🎤 [{elapsed:.1f}s] Đang phân tích: {label_text} ({confidence:.1%})"
        )
        self.audio_status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: bold;
                background-color: #e3f2fd;
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #90caf9;
            }}
        """)

    def start_sound(self):
        """Bắt đầu phát âm thanh"""
        try:
            self.sound_manager = get_sound_manager()
            self.sound_manager.play_alert(loop=True)
            self.sound_started = True
        except Exception as e:
            print(f"⚠️ Không thể phát âm thanh: {e}")

    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Warning icon
        warning_label = QLabel("🚨")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("font-size: 90px; margin: 0px;")

        # Title
        self.title_label = QLabel("NGUY HIỂM!")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Arial', 22, QFont.Bold))
        self.title_label.setStyleSheet("color: #e74c3c; margin: 5px 0px;")

        # Message với line spacing
        message_text = """
        <div style='text-align: center; line-height: 1.6;'>
            <p style='margin: 8px 0; font-size: 14px; color: #2c3e50;'>
                <b>Bạn đã xác nhận buồn ngủ 3 lần liên tiếp!</b>
            </p>
            <p style='margin: 8px 0; font-size: 13px; color: #34495e;'>
                Việc tiếp tục lái xe rất nguy hiểm.
            </p>
            <p style='margin: 8px 0; font-size: 13px; color: #34495e;'>
                Vui lòng dừng lại và nghỉ ngơi!
            </p>
        </div>
        """

        message_label = QLabel(message_text)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.RichText)
        message_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        # Audio status label
        self.audio_status_label = QLabel("🎤 Đang khởi tạo nhận diện giọng nói...")
        self.audio_status_label.setAlignment(Qt.AlignCenter)
        self.audio_status_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.audio_status_label.setStyleSheet("""
            QLabel {
                color: #0066cc;
                background-color: #e3f2fd;
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #90caf9;
            }
        """)

        # Sound indicator
        self.sound_label = QLabel("🚨 ÂM THANH CẢNH BÁO KHẨN CẤP 🚨")
        self.sound_label.setAlignment(Qt.AlignCenter)
        self.sound_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.sound_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #e74c3c;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0px;
            }
        """)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        stop_button = QPushButton("🛑 Dừng lại nghỉ ngơi")
        stop_button.setMinimumHeight(55)
        stop_button.setFont(QFont('Arial', 12, QFont.Bold))
        stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        stop_button.clicked.connect(self.accept_and_stop_sound)

        continue_button = QPushButton("⚠️ Tiếp tục\n(Nguy hiểm)")
        continue_button.setMinimumHeight(55)
        continue_button.setFont(QFont('Arial', 10))
        continue_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7a7b;
            }
        """)
        continue_button.clicked.connect(self.reject_and_stop_sound)

        button_layout.addWidget(stop_button, 65)
        button_layout.addWidget(continue_button, 35)

        # Add to layout
        layout.addWidget(warning_label)
        layout.addWidget(self.title_label)
        layout.addSpacing(5)
        layout.addWidget(message_label)
        layout.addSpacing(5)
        layout.addWidget(self.audio_status_label)
        layout.addWidget(self.sound_label)
        layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border: 4px solid #e74c3c;
                border-radius: 10px;
            }
        """)

        # Blinking timers
        self.title_blink_timer = QTimer()
        self.title_blink_state = True
        self.title_blink_timer.timeout.connect(self.blink_title)
        self.title_blink_timer.start(500)

        self.sound_blink_timer = QTimer()
        self.sound_blink_state = True
        self.sound_blink_timer.timeout.connect(self.blink_sound_label)
        self.sound_blink_timer.start(300)

    def blink_title(self):
        """Nhấp nháy tiêu đề"""
        if self.title_blink_state:
            self.title_label.setStyleSheet("color: #e74c3c; margin: 5px 0px;")
        else:
            self.title_label.setStyleSheet("color: #c0392b; margin: 5px 0px;")
        self.title_blink_state = not self.title_blink_state

    def blink_sound_label(self):
        """Nhấp nháy label âm thanh"""
        if self.sound_blink_state:
            self.sound_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: #e74c3c;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0px;
                }
            """)
        else:
            self.sound_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: #c0392b;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0px;
                }
            """)
        self.sound_blink_state = not self.sound_blink_state

    def accept_and_stop_sound(self):
        """Xác nhận và dừng âm thanh"""
        self.is_timeout = False
        self.stop_sound()
        self.stop_audio_detection()
        self.accept()

    def reject_and_stop_sound(self):
        """Từ chối và dừng âm thanh"""
        self.is_timeout = False
        self.stop_sound()
        self.stop_audio_detection()
        self.reject()

    def stop_sound(self):
        """Dừng âm thanh"""
        try:
            if self.sound_manager and self.sound_started:
                self.sound_manager.stop_alert()
                self.sound_started = False
        except Exception as e:
            print(f"⚠️ Lỗi dừng âm thanh: {e}")

        try:
            self.title_blink_timer.stop()
            self.sound_blink_timer.stop()
        except:
            pass

    def stop_audio_detection(self):
        """Dừng audio detection"""
        if self.audio_worker and self.audio_worker.isRunning():
            self.audio_worker.stop()
            self.audio_worker.wait(1000)

    def closeEvent(self, event):
        """Xử lý khi đóng dialog"""
        self.stop_sound()
        self.stop_audio_detection()
        event.accept()


class ProcessingWorker(QThread):
    """Worker thread để thực hiện công việc xử lý trong background"""
    
    finished = pyqtSignal(bool, str)  # (success, message)
    progress_update = pyqtSignal(str)  # Cập nhật progress message
    
    def __init__(self, process_function=None, *args, **kwargs):
        super().__init__()
        self.process_function = process_function
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Chạy hàm xử lý"""
        try:
            if self.process_function:
                self.progress_update.emit("Đang khởi tạo...")
                result = self.process_function(*self.args, **self.kwargs)
                self.progress_update.emit("Hoàn tất!")
                self.finished.emit(True, "Thành công")
            else:
                # Hàm mặc định (có thể thay đổi)
                self.progress_update.emit("Đang xử lý dữ liệu...")
                import time
                time.sleep(2)  # Giả lập xử lý
                self.progress_update.emit("Đang tải model...")
                time.sleep(2)
                self.progress_update.emit("Hoàn tất!")
                self.finished.emit(True, "Thành công")
        except Exception as e:
            self.finished.emit(False, str(e))


class WaitingDialog(QDialog):
    """Dialog hiển thị khi đang xử lý sau khi đăng nhập"""
    
    def __init__(self, parent=None, process_function=None, *args, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("⏳ Đang xử lý")
        self.setModal(True)
        self.setFixedSize(450, 250)
        
        # Không cho phép đóng dialog khi đang xử lý
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        self.process_function = process_function
        self.process_args = args
        self.process_kwargs = kwargs
        self.worker = None
        
        self.init_ui()
        
        # Bắt đầu xử lý sau khi UI đã sẵn sàng
        QTimer.singleShot(100, self.start_processing)
    
    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Icon loading
        icon_label = QLabel("⏳")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 60px;")
        
        # Title
        title_label = QLabel("Đang trong tiến trình training")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        # Progress message
        self.progress_label = QLabel("Đang khởi tạo hệ thống...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setFont(QFont('Arial', 11))
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #3498db;
                background-color: #ebf5fb;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #3498db;
            }
        """)
        self.progress_label.setWordWrap(True)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        
        # Add to layout
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Style dialog
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 10px;
            }
        """)
    
    def start_processing(self):
        """Bắt đầu xử lý trong worker thread"""
        self.worker = ProcessingWorker(self.process_function, 
                                      *self.process_args, 
                                      **self.process_kwargs)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.start()
    
    def update_progress(self, message):
        """Cập nhật thông báo tiến trình"""
        self.progress_label.setText(message)
        # Cập nhật lại UI
        QTimer.singleShot(10, lambda: None)
    
    def on_processing_finished(self, success, message):
        """Xử lý khi hoàn thành"""
        # Cleanup worker
        if self.worker:
            self.worker.wait()
            self.worker = None
        
        if success:
            self.progress_label.setText("✅ " + message)
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    background-color: #d5f4e6;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #27ae60;
                }
            """)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            # Đóng dialog sau 0.5 giây
            QTimer.singleShot(500, self.accept)
        else:
            self.progress_label.setText("❌ Lỗi: " + message)
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    background-color: #fadbd8;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #e74c3c;
                }
            """)
            # Cho phép đóng dialog khi có lỗi
            self.setWindowFlags(Qt.Dialog)
            QTimer.singleShot(2000, self.reject)
    
    def closeEvent(self, event):
        """Xử lý khi đóng dialog - chỉ cho phép đóng khi đã xong"""
        if self.worker and self.worker.isRunning():
            # Nếu đang chạy, hủy worker
            self.worker.terminate()
            self.worker.wait()
        event.accept()
