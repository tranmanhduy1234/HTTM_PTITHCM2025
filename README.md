# HTTM_PTITHCM2025

## 📋 Mô tả dự án

**HTTM_PTITHCM2025** là hệ thống giám sát camera thông minh sử dụng công nghệ **YOLOv11** để phát hiện trạng thái buồn ngủ của người lái xe và cảnh báo kịp thời, nhằm giảm thiểu tai nạn giao thông do mất tập trung hoặc buồn ngủ.

Dự án được phát triển phục vụ môn học **Phát triển các Hệ thống Thông minh (INT 14151)** tại Học viện Công nghệ Bưu chính Viễn thông.

---

## ✨ Tính năng chính

### 🔐 Xác thực người dùng
- **Đăng nhập / Đăng ký**: Tạo tài khoản riêng biệt cho từng người dùng
- **Quản lý session**: Ghi nhận phiên lái xe, thời gian bắt đầu và kết thúc

### 👁️ Nhận diện buồn ngủ (AI)
- **Phát hiện real-time**: Sử dụng YOLOv11 phân loại ảnh khuôn mặt thành **Drowsy** (buồn ngủ) hoặc **Natural** (bình thường)
- **Xử lý batch**: Tối ưu hiệu năng bằng xử lý nhiều frame cùng lúc
- **Model cá nhân hóa**: Huấn luyện model riêng cho từng user dựa trên ảnh cảnh báo đã lưu

### ⚠️ Cảnh báo và ghi nhận
- **Cảnh báo âm thanh**: Phát âm thanh khi phát hiện buồn ngủ liên tục ≥ 3 giây
- **Lưu trữ dữ liệu**: Tự động lưu frame ảnh cảnh báo vào database và thư mục
- **Tạo video**: Ghép các frame thành video phục vụ xem lại và đánh giá

### 📊 Thống kê & Xem lại
- **Thống kê theo ngày / giờ**: Biểu đồ tần suất buồn ngủ
- **Xem lại video**: Danh sách video cảnh báo, phát video, xác nhận nhãn (đúng/sai) để cải thiện dataset

### 🎤 Xác nhận bằng giọng nói (tuỳ chọn)
- **Conformer Audio Classifier**: Model Conformer phân loại âm thanh để xác nhận trạng thái buồn ngủ qua giọng nói (đang tích hợp)

---

## 🛠️ Công nghệ sử dụng

### Ngôn ngữ & Framework
| Công nghệ | Phiên bản | Mô tả |
|-----------|-----------|-------|
| **Python** | 3.12+ | Ngôn ngữ lập trình chính |
| **PyQt5** | 5.15.11 | Framework GUI desktop |
| **OpenCV** | 4.10–4.11 | Xử lý ảnh, đọc camera, tạo video |

### AI / Machine Learning
| Công nghệ | Phiên bản | Mô tả |
|-----------|-----------|-------|
| **Ultralytics YOLO11** | 8.3.177 | Model phân loại buồn ngủ (classification) |
| **PyTorch** | - | Nền tảng cho Conformer audio |

### Cơ sở dữ liệu & Lưu trữ
| Công nghệ | Mô tả |
|-----------|-------|
| **SQLite** | Cơ sở dữ liệu nhúng (file `app.db`) |
| **FFmpeg / QMediaPlayer** | Phát âm thanh cảnh báo |

### Thư viện bổ sung
- **NumPy**, **SciPy**: Xử lý số học, xử lý tín hiệu
- **PyAudio**, **SoundFile**, **TorchAudio**: Thu âm và xử lý audio (cho Conformer)
- **SHA256**: Mã hóa mật khẩu

---

## 📁 Cấu trúc dự án

```
HTTM_PTITHCM2025/
├── main.py                 # Điểm vào ứng dụng, MainWindow
├── config.json             # Cấu hình camera, model, đường dẫn
├── requirements.txt        # Dependencies Python
├── app.db                  # SQLite database (tự tạo khi chạy)
│
├── core/                   # Logic AI & cấu hình
│   ├── config.py           # Load config.json
│   ├── DrowsinessDetector.py  # YOLO phát hiện buồn ngủ, batch inference
│   ├── model_conformer.py  # Conformer audio classifier
│   ├── Util.py             # Tiền xử lý audio cho Conformer
│   └── best.pt             # Model YOLO mặc định (nếu có)
│
├── views/                  # Giao diện PyQt5
│   ├── LoginView.py        # Đăng nhập + ModelTrainer
│   ├── register_view.py    # Đăng ký tài khoản
│   ├── DashboardView.py    # Camera, log, nút điều khiển
│   ├── statistics_view.py  # Biểu đồ thống kê
│   ├── video_review_view.py # Xem video, xác nhận nhãn
│   └── Dialogs.py          # DrowsinessAlertDialog, RestAlertDialog, WaitingDialog
│
├── services/               # Business logic
│   ├── user_service.py     # Đăng ký, đăng nhập
│   ├── session_service.py  # Quản lý session lái xe
│   └── statistics_service.py # Thống kê theo ngày/giờ
│
├── repository/             # Truy cập dữ liệu
│   ├── user_repo.py
│   ├── session_repo.py
│   ├── drowsy_video_repo.py
│   └── frame_repo.py
│
├── db/
│   └── db.py               # Kết nối SQLite
│
├── utils/
│   ├── sound_manager.py    # Phát âm thanh cảnh báo
│   ├── CameraThread.py     # Thread capture camera + DrowsinessDetector
│   └── VideoManager.py     # Tạo MP4 từ các frame
│
├── assets/                 # Tài nguyên (gitignore)
│   └── alert.mp3           # Âm thanh cảnh báo
│
├── model/                  # Model YOLO theo user (model_{user_id}.pt)
├── drowsy_images/          # Ảnh cảnh báo buồn ngủ (input cho training)
├── tmp_dataset/            # Dataset tạm cho YOLO train
└── runs/                   # Output training Ultralytics
```

---

## 🗄️ Cơ sở dữ liệu (SQLite)

### Các bảng chính

| Bảng | Mô tả |
|------|-------|
| **User** | Thông tin người dùng: `ID`, `userName`, `email`, `password`, `createdAt`, `isActive` |
| **Session** | Phiên lái xe: `ID`, `userID`, `startTime`, `endTime` |
| **DrowsyVideo** | Ghi nhận sự kiện cảnh báo: `ID`, `sessionID`, `startTime`, `endTime`, `userChoiceLabel` |
| **Frame** | Các frame ảnh thuộc mỗi video: `ID`, `drowsyVideoID`, `confidenceScore`, `modelPrediction`, `imageURL` |

---

## 📦 Cài đặt

### Yêu cầu hệ thống

- **Python**: 3.12 trở lên (hoặc Conda)
- **Phần cứng**: Máy tính có camera, loa
- **Hệ điều hành**: Windows / macOS / Linux

### Cài đặt với Python

```bash
# Clone repository
git clone https://github.com/nyvantran/HTTM_PTITHCM2025.git
cd HTTM_PTITHCM2025

# Tạo virtual environment (khuyến nghị)
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### Cài đặt với Conda

```bash
# Clone repository
git clone https://github.com/nyvantran/HTTM_PTITHCM2025.git
cd HTTM_PTITHCM2025

# Tạo môi trường
conda create -n HTTM_PTITHCM2025 python=3.12 -y
conda activate HTTM_PTITHCM2025

# Cài đặt dependencies
pip install -r requirements.txt
```

### Phụ thuộc cho tính năng Audio

Nếu dùng xác nhận bằng giọng nói:

```bash
pip install torch torchaudio pyaudio soundfile
```

---

## 🔧 Cấu hình

Chỉnh sửa file `config.json`:

```json
{
  "assets": {
    "audio_alert": "assets/alert.mp3"
  },
  "drowsy_image_path": "drowsy_images",
  "model_path": "model",
  "camera": {
    "source": 0,
    "frame_width": 640,
    "frame_height": 480,
    "fps": 30
  }
}
```

| Tham số | Mô tả |
|---------|-------|
| `assets.audio_alert` | Đường dẫn file âm thanh cảnh báo |
| `drowsy_image_path` | Thư mục lưu ảnh cảnh báo buồn ngủ |
| `model_path` | Thư mục chứa model YOLO theo user (`model/model_{id}.pt`) |
| `camera.source` | ID camera (0, 1, 2...) hoặc đường dẫn file video |
| `camera.frame_width` | Chiều rộng frame |
| `camera.frame_height` | Chiều cao frame |
| `camera.fps` | Tốc độ khung hình |

---

## 🎯 Cách sử dụng

### Khởi chạy ứng dụng

```bash
python main.py
```

### Luồng sử dụng cơ bản

1. **Đăng nhập** (hoặc đăng ký tài khoản mới)
2. Sau đăng nhập, hệ thống có thể **train model** từ ảnh cảnh báo cũ (nếu có)
3. Vào **Dashboard** → Bấm **Bắt đầu giám sát** để mở camera
4. Khi phát hiện buồn ngủ ≥ 3 giây → phát âm thanh cảnh báo, lưu ảnh và tạo video
5. Xem **Thống kê** hoặc **Xem video** để đánh giá và xác nhận nhãn

### Tài khoản mặc định

- **Username**: `admin`
- **Password**: `admin`

---

## 🏗️ Kiến trúc & Luồng xử lý

### Luồng phát hiện buồn ngủ

1. **CameraThread** đọc frame từ camera (OpenCV)
2. **DrowsinessDetector** nhận frame, đưa vào hàng đợi batch
3. YOLO inference batch → trả về class (Drowsy/Natural) và confidence
4. Nếu tỉ lệ buồn ngủ liên tục vượt ngưỡng 3 giây → gọi callback cảnh báo
5. **frame_queue** lưu các frame liên quan → lưu ảnh, ghi DB, tạo video

### Luồng đào tạo model (ModelTrainer)

1. Thu thập ảnh từ `drowsy_images/drowsy_*_sessionID=*`
2. Phân loại Drowsy / Natural, cân bằng dataset
3. Chia train/test (80/20) vào `tmp_dataset/`
4. Dùng YOLO (`yolo11n-cls.pt` hoặc model cũ) train trên dataset
5. Copy `best.pt` → `model/model_{user_id}.pt`

---

## 🐛 Xử lý lỗi

### Camera không mở được

```bash
# Kiểm tra camera
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

- Đảm bảo không có ứng dụng khác đang chiếm camera
- Thử đổi `source` trong config (1, 2...) nếu có nhiều camera

### Phát hiện kém

- Cải thiện ánh sáng, góc máy
- Huấn luyện lại model với nhiều ảnh mẫu hơn
- Kiểm tra dữ liệu trong `drowsy_images/` đủ và cân bằng

### Thiếu model YOLO

- Lần đầu chạy: cần có sẵn `core/best.pt` hoặc file trong `model/`
- Sau khi có ảnh cảnh báo, đăng nhập sẽ trigger training → tạo `model/model_{user_id}.pt`

### Lỗi âm thanh

- Kiểm tra file `assets/alert.mp3` tồn tại
- Trên Linux có thể cần cài `libqt5multimedia5-plugins` hoặc FFmpeg

---

## 👥 Tác giả

- **TranDoManhDuy** – Developer – [GitHub](https://github.com/TranDoManhDuy)
- **nyvantran** – Developer – [GitHub](https://github.com/nyvantran)
- **HieuITMHG** – Developer – [GitHub](https://github.com/HieuITMHG)

---

## 📄 Giấy phép

Dự án phục vụ mục đích học tập môn Phát triển các Hệ thống Thông minh (INT 14151).

---

⭐ **Nếu dự án hữu ích, hãy cho một star nhé!** ⭐
