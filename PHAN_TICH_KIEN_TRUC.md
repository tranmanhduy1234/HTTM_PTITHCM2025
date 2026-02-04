# PHÂN TÍCH KIẾN TRÚC DỰ ÁN HTTM_PTITHCM2025

## 📋 TỔNG QUAN DỰ ÁN

**HTTM_PTITHCM2025** là một hệ thống giám sát và cảnh báo buồn ngủ cho người lái xe sử dụng công nghệ YOLOv11 (Ultralytics) để phát hiện trạng thái buồn ngủ từ hình ảnh camera. Dự án được phát triển phục vụ môn học Phát triển các Hệ thống Thông minh (INT 14151).

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

### **1. Kiến trúc tổng thể**
- **Ngôn ngữ lập trình**: Python 3.12+
- **Framework GUI**: PyQt5
- **Thư viện xử lý ảnh**: OpenCV (cv2)
- **Thư viện AI/ML**: Ultralytics YOLO11
- **Cơ sở dữ liệu**: SQLite
- **Kiến trúc**: Layered Architecture (Presentation → Service → Repository → Database)

### **2. Cấu trúc thư mục**

```
HTTM_PTITHCM2025/
├── main.py                    # Entry point - MainWindow
├── config.json                # Cấu hình hệ thống
├── requirements.txt           # Dependencies
├── app.db                     # SQLite database
│
├── core/                      # Core AI/ML components
│   ├── DrowsinessDetector.py  # Lớp phát hiện buồn ngủ (YOLO)
│   ├── config.py              # Config manager
│   ├── clever.py              # (Utility)
│   └── best.pt                # YOLO model weights
│
├── db/                        # Database layer
│   ├── db.py                  # Database connection
│   ├── schema.py              # Database schema definition
│   └── schema.jpg             # Schema visualization
│
├── repository/                # Data Access Layer (Repository Pattern)
│   ├── user_repo.py           # User data operations
│   ├── session_repo.py        # Session data operations
│   ├── drowsy_video_repo.py   # Drowsy video data operations
│   ├── frame_repo.py          # Frame data operations
│   ├── dataset_repo.py        # Dataset management
│   └── weight_repo.py         # Model weight management
│
├── services/                  # Business Logic Layer
│   ├── user_service.py        # User business logic
│   ├── session_service.py     # Session management
│   ├── statistics_service.py  # Statistics calculation
│   └── generatorVideo.py     # Video generation service
│
├── views/                     # Presentation Layer (PyQt5 Views)
│   ├── LoginView.py           # Màn hình đăng nhập
│   ├── register_view.py       # Màn hình đăng ký
│   ├── DashboardView.py       # Màn hình chính - giám sát
│   ├── statistics_view.py     # Màn hình thống kê
│   ├── video_review_view.py   # Màn hình xem lại video
│   └── Dialogs.py             # Dialog components
│
├── utils/                     # Utility classes
│   ├── CameraThread.py        # Thread xử lý camera (QThread)
│   ├── sound_manager.py       # Quản lý âm thanh cảnh báo
│   └── VideoManager.py        # Quản lý video
│
├── assets/                    # Static resources
│   ├── alert.mp3              # File âm thanh cảnh báo
│   └── alert.mav              # Alternative audio format
│
└── drowsy_images/            # Thư mục lưu ảnh cảnh báo
    └── drowsy_YYYYMMDD_HHMMSS_sessionID=X/
        └── frame_idx=...jpg
```

---

## 🎯 CÁC LỚP KIẾN TRÚC (LAYERS)

### **1. Presentation Layer (Views)**

#### **MainWindow (main.py)**
- **Vai trò**: Điều phối toàn bộ ứng dụng, quản lý navigation giữa các views
- **Pattern**: Singleton (một instance duy nhất)
- **Tính năng**:
  - Quản lý `QStackedWidget` để chuyển đổi giữa các views
  - Lazy loading cho Statistics và Video Review views
  - Quản lý session lifecycle
  - Cleanup resources khi đóng ứng dụng

#### **LoginView**
- Xác thực người dùng
- Chuyển hướng đến Register hoặc Dashboard

#### **RegisterView**
- Đăng ký tài khoản mới
- Validation input

#### **DashboardView**
- **Vai trò**: Màn hình chính - hiển thị camera và giám sát buồn ngủ
- **Tính năng**:
  - Hiển thị video stream từ camera
  - Hiển thị thông tin trạng thái (confidence, drowsy ratio)
  - Quản lý camera thread
  - Hiển thị log cảnh báo
  - Điều khiển start/stop monitoring
  - Hiển thị thời gian lái xe

#### **StatisticsView**
- Hiển thị thống kê theo thời gian
- Phân tích dữ liệu buồn ngủ

#### **VideoReviewView**
- Xem lại các video cảnh báo đã lưu
- Xác nhận/sửa label cảnh báo

---

### **2. Service Layer**

#### **SessionService**
- Quản lý session lifecycle (start/end)
- Liên kết session với user

#### **UserService**
- Business logic cho user operations
- Authentication logic

#### **StatisticsService**
- Tính toán thống kê từ database
- Aggregation dữ liệu

#### **VideoGeneratorService**
- Tạo video từ các frame đã lưu
- Export video cho review

---

### **3. Repository Layer (Data Access)**

**Pattern**: Repository Pattern - Tách biệt data access logic

#### **user_repo.py**
- `create_user()`, `get_user_by_email()`, `authenticate_user()`

#### **session_repo.py**
- `create_session()`, `end_session()`, `get_sessions_by_user()`

#### **drowsy_video_repo.py**
- `create_drowsy_video()`, `get_drowsy_videos()`, `update_user_choice()`

#### **frame_repo.py**
- `insert_frame()`, `get_frames_by_video()`

#### **dataset_repo.py**
- Quản lý dataset cho training
- Quản lý frame limit per user

#### **weight_repo.py**
- Quản lý model weights
- Version control cho models

---

### **4. Core Layer (AI/ML)**

#### **DrowsinessDetector**
- **Vai trò**: Lớp chính xử lý phát hiện buồn ngủ
- **Kiến trúc**:
  - **Multi-threading**: Sử dụng 2 threads riêng biệt
    - `_processing_loop()`: Xử lý YOLO model (batch processing)
    - `_save_img()`: Lưu ảnh/video cảnh báo
  - **Queue-based processing**: 
    - `processing_queue`: Hàng đợi frames chờ xử lý
    - `result_queue`: Hàng đợi kết quả đã xử lý
    - `frame_queue`: Hàng đợi frames để lưu trữ
  - **State management**:
    - `drowsy_history`: Lịch sử phát hiện buồn ngủ (deque)
    - `confidence_history`: Lịch sử confidence scores
    - `alert_active`: Trạng thái cảnh báo hiện tại

- **Thuật toán phát hiện**:
  1. Nhận frame từ camera
  2. Đưa vào `processing_queue`
  3. Xử lý batch qua YOLO model
  4. Cập nhật `drowsy_history` và `confidence_history`
  5. Tính `drowsy_ratio` = tỷ lệ buồn ngủ trong 30 frames gần nhất
  6. Nếu `drowsy_ratio > 0.7` và kéo dài >= `alert_threshold` (3 giây):
     - Kích hoạt cảnh báo
     - Lưu frames vào database
     - Gọi callback để phát âm thanh

- **Tối ưu hóa**:
  - Batch processing (mặc định batch_size=4)
  - Queue với maxsize để tránh memory overflow
  - Cooldown period (10 giây) giữa các cảnh báo
  - Lazy frame saving (chỉ lưu khi có cảnh báo)

---

### **5. Utility Layer**

#### **CameraThread (QThread)**
- **Vai trò**: Thread riêng để đọc camera và xử lý frames
- **Signals**:
  - `frame_ready`: Emit frame đã xử lý
  - `drowsiness_alert`: Emit khi có cảnh báo
  - `error_occurred`: Emit khi có lỗi
- **Tính năng**:
  - Đọc frames từ camera (OpenCV)
  - Gọi `detector.process_frame()`
  - Convert OpenCV frame → QPixmap
  - Giới hạn FPS (~30 FPS)

#### **SoundManager**
- Phát âm thanh cảnh báo
- Quản lý audio resources

#### **VideoManager**
- Tạo video từ frames
- Quản lý video files

---

## 🗄️ DATABASE SCHEMA

### **Các bảng chính**:

1. **User**
   - `ID` (PK)
   - `userName`, `password`, `email`
   - `createdAt`, `isActive`

2. **Dataset**
   - `ID` (PK)
   - `userID` (FK → User)
   - `frameLimit`: Giới hạn số frame user có thể sử dụng
   - `status`: 'SPENDING' hoặc 'USED'
   - `expiresAt`, `createdAt`

3. **Weight**
   - `ID` (PK)
   - `userID` (FK → User)
   - `datasetID` (FK → Dataset)
   - `storageURL`: Đường dẫn file model
   - `isCurrentlyUse`: Model đang được sử dụng

4. **Session**
   - `ID` (PK)
   - `userID` (FK → User)
   - `startTime`, `endTime`

5. **DrowsyVideo**
   - `ID` (PK)
   - `sessionID` (FK → Session)
   - `startTime`, `endTime`
   - `userChoiceLabel`: User xác nhận cảnh báo đúng/sai

6. **Frame**
   - `ID` (PK)
   - `drowsyVideoID` (FK → DrowsyVideo)
   - `confidenceScore`: Confidence từ model
   - `modelPrediction`: True/False (drowsy/natural)
   - `imageURL`: Đường dẫn ảnh frame
   - `datasetID` (FK → Dataset) - để đánh dấu frame dùng cho training
   - `createdAt`

### **Relationships**:
- User → Session: One-to-Many
- Session → DrowsyVideo: One-to-Many
- DrowsyVideo → Frame: One-to-Many
- User → Dataset: One-to-Many
- Dataset → Frame: One-to-Many (để đánh dấu frame dùng cho training)
- User → Weight: One-to-Many

---

## 🔄 QUY TRÌNH VẬN HÀNH

### **1. Quy trình khởi động ứng dụng**

```
1. main.py → MainWindow.__init__()
   ↓
2. Khởi tạo essential views (Login, Register, Dashboard)
   ↓
3. Hiển thị LoginView
   ↓
4. User đăng nhập
   ↓
5. UserService.authenticate() → user_repo.authenticate_user()
   ↓
6. SessionService.start_session() → session_repo.create_session()
   ↓
7. Chuyển sang DashboardView
   ↓
8. User click "Bắt đầu giám sát"
   ↓
9. DashboardView.start_monitoring()
   - Tạo DrowsinessDetector
   - Tạo CameraThread
   - Kết nối signals
   - Start camera thread
```

### **2. Quy trình phát hiện buồn ngủ**

```
1. CameraThread đọc frame từ camera
   ↓
2. CameraThread → detector.process_frame(frame)
   ↓
3. DrowsinessDetector:
   - Đưa frame vào processing_queue
   ↓
4. Thread _processing_loop():
   - Thu thập batch frames (batch_size=4)
   - Gọi model.predict(batch)
   - Đưa kết quả vào result_queue
   ↓
5. process_frame() nhận kết quả từ result_queue
   ↓
6. _update_drowsy_state():
   - Cập nhật drowsy_history, confidence_history
   - Tính drowsy_ratio
   - Kiểm tra điều kiện cảnh báo:
     * drowsy_ratio > 0.7
     * Kéo dài >= 3 giây
     * Đã qua cooldown period
   ↓
7. Nếu đủ điều kiện:
   - _trigger_alert()
   - Gọi callback → CameraThread.drowsiness_alert signal
   - Set is_save_img = True
   ↓
8. Thread _save_img():
   - Lưu frames từ frame_queue vào thư mục
   - Tạo DrowsyVideo record
   - Tạo Frame records
   - VideoManager tạo video file
   ↓
9. DashboardView nhận drowsiness_alert signal:
   - Hiển thị dialog cảnh báo
   - SoundManager phát âm thanh
   - Cập nhật log table
```

### **3. Quy trình xem thống kê**

```
1. User click "📊 Thống kê"
   ↓
2. MainWindow.show_statistics() (lazy load)
   ↓
3. StatisticsView được khởi tạo
   ↓
4. StatisticsService.get_statistics(user_id)
   ↓
5. Query database qua repositories:
   - session_repo.get_sessions_by_user()
   - drowsy_video_repo.get_drowsy_videos_by_user()
   - frame_repo.get_frames_by_user()
   ↓
6. Tính toán thống kê:
   - Số lần cảnh báo
   - Thời gian lái xe
   - Tỷ lệ buồn ngủ
   - Biểu đồ theo thời gian
   ↓
7. Hiển thị trên StatisticsView
```

### **4. Quy trình xem lại video**

```
1. User click "🎬 Xem video"
   ↓
2. MainWindow.show_videos() (lazy load)
   ↓
3. VideoReviewView được khởi tạo
   ↓
4. Query drowsy_video_repo.get_drowsy_videos_by_user()
   ↓
5. Hiển thị danh sách videos
   ↓
6. User chọn video:
   - Load frames từ frame_repo
   - VideoManager.load_video() hoặc tạo từ frames
   ↓
7. User xem và xác nhận label:
   - Update userChoiceLabel trong DrowsyVideo
   - Có thể đánh dấu frame cho dataset training
```

---

## 🔧 CÔNG NGHỆ VÀ THƯ VIỆN

### **Core Dependencies**:
- **PyQt5** (5.15.11): GUI framework
- **OpenCV** (4.11.0.86): Xử lý ảnh và video
- **Ultralytics** (8.3.177): YOLO11 model inference
- **NumPy** (2.3.4): Xử lý số học
- **SciPy** (1.16.2): Scientific computing

### **Python Standard Library**:
- `threading`: Multi-threading
- `queue`: Queue management
- `sqlite3`: Database
- `datetime`: Time handling
- `pathlib`: File path management
- `json`: Config file parsing

---

## 🎨 DESIGN PATTERNS

### **1. Repository Pattern**
- Tách biệt data access logic khỏi business logic
- Dễ dàng thay đổi database hoặc thêm caching layer

### **2. Service Layer Pattern**
- Business logic tập trung trong service layer
- Views chỉ gọi services, không trực tiếp gọi repositories

### **3. Observer Pattern (Signals & Slots)**
- PyQt5 signals/slots cho communication giữa threads
- CameraThread emit signals → DashboardView nhận và cập nhật UI

### **4. Strategy Pattern (implicit)**
- Có thể thay đổi model (best.pt) mà không thay đổi code detector

### **5. Singleton Pattern**
- Config manager (core.config)
- Database connection (db.db)

### **6. Factory Pattern (implicit)**
- Repository factory pattern qua `get_connection()`

---

## ⚡ TỐI ƯU HÓA VÀ PERFORMANCE

### **1. Multi-threading**
- **CameraThread**: Đọc camera độc lập với UI thread
- **DrowsinessDetector._processing_loop**: Xử lý YOLO độc lập
- **DrowsinessDetector._save_img**: Lưu ảnh độc lập

### **2. Batch Processing**
- Xử lý nhiều frames cùng lúc (batch_size=4)
- Giảm overhead của model inference

### **3. Queue Management**
- Bounded queues (maxsize) để tránh memory overflow
- Non-blocking operations (`put_nowait`, `get_nowait`)

### **4. Lazy Loading**
- StatisticsView và VideoReviewView chỉ load khi cần
- Giảm thời gian khởi động

### **5. Frame Buffering**
- `cv2.CAP_PROP_BUFFERSIZE = 1`: Giảm latency
- Chỉ lưu frames khi có cảnh báo

### **6. Cooldown Mechanism**
- Tránh spam cảnh báo (10 giây cooldown)

---

## 🔐 BẢO MẬT VÀ XÁC THỰC

### **1. User Authentication**
- Password được lưu trong database (nên hash bằng bcrypt)
- Email unique constraint

### **2. Session Management**
- Mỗi user có session riêng
- Session được ghi lại start/end time

### **3. Data Privacy**
- Ảnh cảnh báo được lưu theo session
- Chỉ user sở hữu session mới xem được

---

## 📊 XỬ LÝ DỮ LIỆU VÀ AI/ML

### **1. Model Architecture**
- **YOLO11** (Ultralytics)
- **Input**: RGB image frames (640x480)
- **Output**: Classification (Drowsy/Natural) + Confidence score

### **2. Data Pipeline**
```
Camera → OpenCV Frame → DrowsinessDetector → YOLO Model → Classification
                                                              ↓
                                                      Update History
                                                              ↓
                                                      Calculate Ratio
                                                              ↓
                                                      Alert Decision
```

### **3. Training Data Management**
- Frames có thể được đánh dấu cho dataset (datasetID)
- User có thể xác nhận label (userChoiceLabel)
- Frame limit per user để quản lý dataset size

---

## 🎯 ĐIỂM MẠNH CỦA DỰ ÁN

1. ✅ **Kiến trúc rõ ràng**: Layered architecture dễ maintain
2. ✅ **Multi-threading**: Xử lý camera và AI độc lập, không block UI
3. ✅ **Batch processing**: Tối ưu performance cho YOLO inference
4. ✅ **Queue-based**: Quản lý memory tốt với bounded queues
5. ✅ **Repository Pattern**: Dễ test và thay đổi database
6. ✅ **Lazy loading**: Tối ưu thời gian khởi động
7. ✅ **Session management**: Theo dõi được từng phiên làm việc
8. ✅ **Data collection**: Hỗ trợ thu thập dữ liệu cho training
9. ✅ **User feedback**: Cho phép user xác nhận cảnh báo đúng/sai

---

## 🔍 ĐIỂM CẦN CẢI THIỆN

1. ⚠️ **Password Security**: Nên hash password bằng bcrypt thay vì lưu plaintext
2. ⚠️ **Error Handling**: Cần thêm try-catch và error logging chi tiết hơn
3. ⚠️ **Configuration**: Nên validate config.json khi load
4. ⚠️ **Testing**: Chưa có unit tests hoặc integration tests
5. ⚠️ **Logging**: Nên sử dụng logging module thay vì print()
6. ⚠️ **Model Management**: Có thể thêm version control cho models
7. ⚠️ **Performance Monitoring**: Chưa có metrics cho FPS, latency
8. ⚠️ **Database Migration**: Chưa có migration system cho schema changes
9. ⚠️ **Documentation**: Cần thêm docstrings cho các methods
10. ⚠️ **Code Duplication**: Một số logic có thể refactor thành utility functions

---

## 🚀 HƯỚNG PHÁT TRIỂN

### **Ngắn hạn**:
- Thêm password hashing (bcrypt)
- Cải thiện error handling và logging
- Thêm unit tests cho core components
- Validation cho config.json

### **Trung hạn**:
- Thêm metrics và performance monitoring
- Database migration system
- Model versioning và A/B testing
- Export/Import dữ liệu

### **Dài hạn**:
- Web dashboard cho remote monitoring
- Real-time alerts qua email/SMS
- Integration với IoT devices
- Cloud deployment
- Multi-camera support
- Advanced analytics và ML insights

---

## 📝 KẾT LUẬN

Dự án **HTTM_PTITHCM2025** là một hệ thống phát hiện buồn ngủ hoàn chỉnh với:
- Kiến trúc layered rõ ràng, dễ maintain
- Multi-threading và batch processing cho performance tốt
- Repository pattern cho data access
- YOLO11 model cho phát hiện chính xác
- Session management và data collection

Đây là một dự án đồ án tốt, thể hiện được kiến thức về:
- Lập trình hướng đối tượng
- Multi-threading và concurrency
- Computer Vision và Deep Learning
- Database design
- GUI development với PyQt5
- Software architecture patterns

---

## 📚 TÀI LIỆU THAM KHẢO

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Ultralytics YOLO](https://docs.ultralytics.com/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**Tác giả**: TranDoManhDuy, nyvantran, HieuITMHG  
**Môn học**: Phát triển các Hệ thống Thông minh (INT 14151)  
**Trường**: PTITHCM

