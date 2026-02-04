from PyQt5.QtCore import QObject, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import os
import sys
import numpy as np
import core.config as config
from pathlib import Path


class AlertSoundManager(QObject):
    """Class quản lý âm thanh cảnh báo"""

    def __init__(self):
        super().__init__()
        self.player = None
        self.sound_file = None
        self.is_playing = False
        self.loop_enabled = False

        # Tìm hoặc tạo file âm thanh
        self._setup_sound_file()

    def _setup_sound_file(self):
        """Tìm hoặc tạo file âm thanh cảnh báo"""
        # Tìm file âm thanh có sẵn
        possible_files = [
            config.config.get("assets")["audio_alert"],
            'sounds/alert.wav',
            'sounds/alert.mp3',

        ]

        for file_path in possible_files:
            if os.path.exists(file_path):
                self.sound_file = os.path.abspath(file_path)
                print(f"✅ Sử dụng file âm thanh: {self.sound_file}")
                return

        # Nếu không tìm thấy, tạo file beep đơn giản
        print("📢 Không tìm thấy file âm thanh, tạo file mặc định...")
        self.sound_file = self._create_beep_sound()

    def _create_beep_sound(self):
        """Tạo file beep đơn giản bằng numpy và scipy"""
        try:
            from scipy.io import wavfile

            # Tạo thư mục sounds
            Path("sounds").mkdir(exist_ok=True)

            # Tham số âm thanh
            sample_rate = 44100  # Hz
            duration = 0.5  # giây
            frequency = 1000  # Hz (cao độ)

            # Tạo sóng sin
            t = np.linspace(0, duration, int(sample_rate * duration))

            # Tạo beep với fade in/out
            beep = np.sin(2 * np.pi * frequency * t)

            # Fade in/out để tránh click sound
            fade_samples = int(0.05 * sample_rate)  # 50ms fade
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)

            beep[:fade_samples] *= fade_in
            beep[-fade_samples:] *= fade_out

            # Convert to 16-bit PCM
            beep_int16 = np.int16(beep * 32767)

            # Lưu file
            output_file = os.path.abspath("sounds/alert.wav")
            wavfile.write(output_file, sample_rate, beep_int16)

            print(f"✅ Đã tạo file âm thanh: {output_file}")
            return output_file

        except ImportError:
            print("⚠️ Không thể tạo file âm thanh (cần scipy)")
            print("   Cài đặt: pip install scipy")
            return None
        except Exception as e:
            print(f"⚠️ Lỗi tạo file âm thanh: {e}")
            return None

    def play_alert(self, loop=True):
        """
        Phát âm thanh cảnh báo
        Args:
            loop: True = phát lặp lại, False = phát 1 lần
        """
        if self.is_playing:
            # Đã đang phát, không cần phát lại
            return

        if not self.sound_file or not os.path.exists(self.sound_file):
            # Fallback to system beep
            print("⚠️ Không tìm thấy file âm thanh, dùng system beep")
            self._play_system_beep()
            return

        try:
            # Khởi tạo QMediaPlayer nếu chưa có
            if self.player is None:
                self.player = QMediaPlayer()
                self.player.mediaStatusChanged.connect(self._on_media_status_changed)
                self.player.error.connect(self._on_error)

            # Set media
            url = QUrl.fromLocalFile(self.sound_file)
            content = QMediaContent(url)
            self.player.setMedia(content)

            # Set volume
            self.player.setVolume(70)  # 0-100

            # Enable loop
            self.loop_enabled = loop

            # Play
            self.player.play()
            self.is_playing = True

            print(f"🔊 Bắt đầu phát âm thanh cảnh báo")

        except Exception as e:
            print(f"⚠️ Lỗi phát âm thanh: {e}")
            import traceback
            traceback.print_exc()
            self._play_system_beep()

    def _on_media_status_changed(self, status):
        """Callback khi trạng thái media thay đổi"""
        try:
            if status == QMediaPlayer.EndOfMedia:
                if self.loop_enabled and self.is_playing:
                    # Replay khi kết thúc
                    self.player.play()
                else:
                    self.is_playing = False
        except Exception as e:
            print(f"⚠️ Lỗi trong _on_media_status_changed: {e}")

    def _on_error(self, error):
        """Callback khi có lỗi"""
        if self.player:
            error_string = self.player.errorString()
            print(f"⚠️ Media Player Error: {error} - {error_string}")
            self.is_playing = False

    def stop_alert(self):
        """Dừng âm thanh cảnh báo"""
        if not self.is_playing:
            return

        try:
            self.loop_enabled = False
            self.is_playing = False

            if self.player:
                self.player.stop()

            print("🔇 Đã dừng âm thanh cảnh báo")

        except Exception as e:
            print(f"⚠️ Lỗi dừng âm thanh: {e}")

    def _play_system_beep(self):
        """Phát beep của hệ thống (fallback)"""
        try:
            if sys.platform == 'win32':
                import winsound
                # Beep 1000Hz, 500ms - chỉ 1 lần
                winsound.Beep(1000, 500)
            else:
                # Linux/Mac
                print('\a')  # Bell character
        except Exception as e:
            print(f"⚠️ Không thể phát system beep: {e}")

    def cleanup(self):
        """Dọn dẹp resources"""
        try:
            self.stop_alert()

            if self.player:
                # Disconnect signals
                try:
                    self.player.mediaStatusChanged.disconnect()
                    self.player.error.disconnect()
                except:
                    pass

                self.player.deleteLater()
                self.player = None

        except Exception as e:
            print(f"⚠️ Lỗi cleanup sound manager: {e}")


# Singleton instance
_sound_manager = None


def get_sound_manager():
    """Lấy instance singleton của SoundManager"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = AlertSoundManager()
    return _sound_manager


def cleanup_sound_manager():
    """Dọn dẹp sound manager"""
    global _sound_manager
    if _sound_manager is not None:
        _sound_manager.cleanup()
        _sound_manager = None
