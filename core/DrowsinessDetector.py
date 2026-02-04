import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import time
import sqlite3
from datetime import datetime
from pathlib import Path
import threading
import queue
import os
import repository.drowsy_video_repo as drowsy_video_repo
import repository.frame_repo as frame_repo
import core.config as config
from utils.VideoManager import VideoManager


class DrowsinessDetector:
    def __init__(self, model_path, batch_size=4, alert_threshold=3, callback=None, **kwargs):
        """
        Args:
            model_path: Đường dẫn đến model YOLO
            batch_size: Số frame xử lý cùng lúc
            alert_threshold: Thời gian liên tục buồn ngủ (giây) trước khi cảnh báo
            callback: Hàm callback khi có cảnh báo (callback_func(frame, drowsy_ratio, avg_conf))
        """
        self.model = YOLO(model_path)
        self.batch_size = batch_size
        self.alert_threshold = alert_threshold
        self.callback = callback

        self.drowsy_history = deque(maxlen=int(30 * alert_threshold)) # Lịch sử phát hiện buồn ngủ
        self.confidence_history = deque(maxlen=int(30 * alert_threshold)) # confidence score tương ứng với các lần ghi nhận trong hàng đợi drowsy history phía trên
        # Lưu trữ kết quả phân loại gần đây
        self.drowsy_history = deque(maxlen=int(30 * alert_threshold))
        self.natural_history = deque(maxlen=int(30 * alert_threshold))
        self.confidence_history = deque(maxlen=int(30 * alert_threshold))

        self.alert_active = False
        self.alert_start_time = None
        self.last_alert_time = 0 # Lần cuối cùng alert
        self.alert_cooldown = 10

        # Trạng thái khởi tạo
        self.current_class = "Unknown"
        self.current_confidence = 0.0
        self.drowsy_ratio = 0.0

        self.processing_queue = queue.Queue(maxsize=30) # Hàng đợi cho (idx, frame)
        self.result_queue = queue.Queue(maxsize=30) # hàng kết quả (rs - frame)
        self.frame_queue = queue.Queue(maxsize=90) # hàng đợi - (rs - frame) phục vụ cho lưu trữ
        self.is_save_img = False # Quyết định lưu frame hình
        self.current_frame_id = None # Frame id hiện tại
        self.last_frame_id = None # frame id cuối trước đó
        self.session_id = kwargs.get("session_id") # Phiên làm việc

        # load các config: model - path image - camera
        self.drowsy_path = config.config.get('drowsy_image_path', 'drowsy_images')
        Path(self.drowsy_path).mkdir(exist_ok=True)

        # Thread xử lý YOLO
        self.running = True
        self.thread = threading.Thread(target=self._processing_loop, daemon=True) 
        self.thread.start()
        # Thread lưu ảnh video
        self.video_manager = VideoManager()
        self.img_thread = threading.Thread(target=self._save_img, daemon=True)
        self.img_thread.start()

    def _save_img(self):
        """Lưu ảnh cảnh báo"""
        while self.running:
            time.sleep(1)
            if self.is_save_img:
                timestamp = self.current_frame_id
                last_id = self.last_frame_id
                video_frame_id = f"{self.drowsy_path}/drowsy_{timestamp}_sessionID={self.session_id}"
                os.makedirs(video_frame_id, exist_ok=True)
                drowsyVideoID = drowsy_video_repo.create_drowsy_video(self.session_id, last_id, timestamp)
                
                for i, (idx, _, confidence, class_name, frame) in enumerate(list(self.frame_queue.queue.copy())):
                    url_img = f"{video_frame_id}/frame_idx={idx}_{i}_confidence={confidence}_class={class_name}.jpg"
                    cv2.imwrite(url_img, frame)
                    frame_repo.insert_frame(drowsyVideoID, confidence, class_name.lower() == 'drowsy', url_img)
                self.video_manager.get_drowsy_video(drowsyVideoID)
                self.is_save_img = False

    def _processing_loop(self):
        """Luồng riêng xử lý YOLO"""
        while self.running:
            frames = []
            frame_indices = []

            # Thu thập batch frames
            while len(frames) < self.batch_size and not self.processing_queue.empty():
                try:
                    idx, frame = self.processing_queue.get(timeout=0.01)
                    frames.append(frame)
                    frame_indices.append(idx)
                except queue.Empty:
                    break

            if not frames:
                time.sleep(0.01)
                continue

            # Xử lý batch
            results = self.model(frames, verbose=False)

            # Lấy kết quả ứng với idx ban đầu
            for idx, result in zip(frame_indices, results):
                # Lấy class và confidence
                class_id = result.probs.top1
                class_name = result.names[class_id]
                confidence = result.probs.top1conf.item()

                # Kiểm tra nếu là Drowsy
                is_drowsy = class_name.lower() == 'drowsy'

                # Đưa kết quả vào result_queue
                try:
                    self.result_queue.put_nowait((idx, is_drowsy, confidence, class_name, result.orig_img))
                    if self.frame_queue.full():
                        self.last_frame_id = self.frame_queue.get_nowait()[0] # lấy ra frame xử lý sớm nhất mà chưa được xuất hình
                    self.frame_queue.put_nowait((idx, is_drowsy, confidence, class_name, result.orig_img.copy()))
                except queue.Full:
                    if self.result_queue.full():
                        self.result_queue.get_nowait()
                    else:
                        self.frame_queue.get_nowait()
    
    # Tiến trình gửi các frame hình vào hàng đợi xử lý + xử lý hàng đợi đã qua model, vẽ lên ảnh thông số hiển thị
    def process_frame(self, frame):
        """
        Xử lý một frame
        Returns: (processed_frame, status_dict)
        """
        # Gửi frame vào queue xử lý
        id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self.processing_queue.full():
            try:
                self.processing_queue.put_nowait((id, frame.copy()))
            except queue.Full:
                pass
        # Nhận kết quả từ queue
        try:
            while not self.result_queue.empty():
                idx, is_drowsy, confidence, class_name, _ = self.result_queue.get_nowait()
                self._update_drowsy_state(idx, is_drowsy, confidence, class_name, frame)
        except queue.Empty:
            pass

        # Tính toán các thông số
        self.drowsy_ratio = sum(self.drowsy_history) / len(self.drowsy_history) if self.drowsy_history else 0
        avg_conf = np.mean(list(self.confidence_history)) if self.confidence_history else 0

        # Vẽ overlay
        frame_display = self._draw_overlay(frame.copy(), self.drowsy_ratio, avg_conf)

        # Trả về frame và status
        status = {
            'class': self.current_class,
            'confidence': self.current_confidence,
            'drowsy_ratio': self.drowsy_ratio,
            'alert_active': self.alert_active,
            'alert_progress': self._get_alert_progress()
        }

        return frame_display, status

    def _update_drowsy_state(self, idx, is_drowsy, confidence, class_name, frame):
        """Cập nhật trạng thái buồn ngủ"""
        self.current_class = class_name
        self.current_confidence = confidence
        self.drowsy_history.append(int(is_drowsy))
        self.natural_history.append(int(not is_drowsy))
        self.confidence_history.append(confidence)

        # Tính tỷ lệ drowsy trong lịch sử gần đây
        if len(self.drowsy_history) >= 30:
            drowsy_ratio = sum(self.drowsy_history) / len(self.drowsy_history)
            avg_conf = np.mean(list(self.confidence_history))

            current_time = time.time()

            # Kiểm tra điều kiện cảnh báo
            if drowsy_ratio > 0.7 and not self.alert_active:
                if self.alert_start_time is None:
                    self.alert_start_time = current_time

                # Nếu đã buồn ngủ liên tục đủ lâu
                elapsed = current_time - self.alert_start_time
                if elapsed >= self.alert_threshold:
                    # Kiểm tra cooldown
                    if current_time - self.last_alert_time > self.alert_cooldown:
                        self.current_frame_id = idx
                        self.is_save_img = True
                        self._trigger_alert(frame, drowsy_ratio, avg_conf)
                        self.last_alert_time = current_time
            else:
                # Reset nếu không còn buồn ngủ
                if drowsy_ratio <= 0.5:
                    self.alert_start_time = None
                natural_ratio = sum(self.natural_history) / len(self.natural_history)
                avg_conf = np.mean(list(self.confidence_history))
                if natural_ratio > 0.8 and avg_conf > 0.8:
                    self.current_frame_id = idx
                    self.is_save_img = True
                    print("✅ Người dùng tỉnh táo, đã lưu trạng thái.")

    def _trigger_alert(self, frame, drowsy_ratio, avg_conf):
        """Kích hoạt cảnh báo"""

        # Gọi callback nếu có
        if self.callback:
            self.callback(frame.copy(), drowsy_ratio, avg_conf)

        # Reset trạng thái sau 2 giây
        def reset_alert():
            time.sleep(2)
            self.alert_active = False

        threading.Thread(target=reset_alert, daemon=True).start()

    def _get_alert_progress(self):
        """Lấy tiến trình cảnh báo (0-1)"""
        #   
        if self.alert_start_time is None:
            return 0.0
        elapsed = time.time() - self.alert_start_time
        return min(elapsed / self.alert_threshold, 1.0)

    def _draw_overlay(self, frame, drowsy_ratio, avg_conf):
        """Vẽ overlay lên frame"""
        # Background cho text
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (400, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Trạng thái hiện tại
        status_text = "DROWSY ⚠️" if self.alert_active else self.current_class
        status_color = (0, 0, 255) if self.alert_active else (0, 255, 0)

        cv2.putText(frame, f"Status: {status_text}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

        # Confidence
        cv2.putText(frame, f"Confidence: {self.current_confidence * 100:.1f}%", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Drowsy ratio
        ratio_color = (0, 0, 255) if drowsy_ratio > 0.7 else (0, 165, 255) if drowsy_ratio > 0.3 else (0, 255, 0)
        cv2.putText(frame, f"Drowsy Ratio: {drowsy_ratio * 100:.1f}%", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, ratio_color, 2)

        # Progress bar
        progress = self._get_alert_progress()
        if progress > 0:
            bar_width = int(380 * progress)
            cv2.rectangle(frame, (10, 110), (10 + bar_width, 130), (0, 140, 255), -1)
            cv2.rectangle(frame, (10, 110), (390, 130), (255, 255, 255), 2)

        return frame

    def get_latest_alerts(self, limit=50):
        """Lấy danh sách cảnh báo gần nhất từ database"""
        cursor = self.conn.cursor()
        cursor.execute('''
                       SELECT timestamp, duration, confirmed, drowsy_ratio, confidence_avg, notes
                       FROM alerts
                       ORDER BY id DESC
                           LIMIT ?
                       ''', (limit,))
        return cursor.fetchall()

    def update_alert_confirmation(self, timestamp, confirmed):
        """Cập nhật xác nhận cảnh báo"""
        drowsy_video_repo.update_user_choice_by_start_time(timestamp, confirmed)

    def stop(self):
        """Dừng detector"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2)
        if self.img_thread.is_alive():
            self.img_thread.join(timeout=2)
        # self.conn.close()
