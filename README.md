# # HTTM_PTITHCM2025

## 📋 Mô tả dự án

Dự án HTTM_PTITHCM2025 là một hệ thống giám sát camera sử dụng công nghệ YOLOv11 để phát hiện sự buồn ngủ của người lái
xe và cảnh báo kịp thời nhằm giảm thiểu tai nạn giao thông do buồn ngử
Dự án được tạo nhằm phục vụ cho môn phát triển các hệ thống thông minh(INT 14151)

## ✨ Tính năng chính

- **Đăng nhập, đăng ký**: tạo sự chuyên biệt riêng cho từng người dùng
- **Nhận diện trạng thái buồn ngủ**: Dựa vào hình ảnh để xác định tài xế có đang buồn ngủ hay không
- **Cảnh báo buồn ngủ**: Phát âm thanh cảnh báo khi phát hiện tài xế buồn ngủ quá 3 giây . Lưu cảnh báo vào database và
  ghi lại hình ảnh để thực hiện cá nhân khóa về sau.(chưa xong)

## 🚀 Công nghệ sử dụng

- **Ngôn ngữ lập trình**: Python
- **Framework GUI**: PyQt5
- **Thư viện xử lý ảnh**: OpenCV
- **Thư viện chạy model AI**: ultralytics YOLO11
- **Cơ sở dữ liệu**: SQLite
- **Phát âm thanh cảnh báo**: ffplay (một phần của FFmpeg của hệ điều hành)

## 📦 Cài đặt

### Yêu cầu hệ thống

- Python version 3.12 trở lên hoặc conda
- DeskTop có kết nối tới camera, loa
- Windows/macOS/Linux

### Cài đặt dependencies

đối với python

```bash
# Clone repository
git clone https://github.com/nyvantran/HTTM_PTITHCM2025.git
cd HTTM_PTITHCM2025

# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

đối với conda

```bash
# Clone repository
git clone https://github.com/nyvantran/HTTM_PTITHCM2025.git
cd HTTM_PTITHCM2025

# Tạo virtual environment (khuyến nghị)
conda create -n HTTM_PTITHCM2025 python=3.12 -y
conda activate HTTM_PTITHCM2025

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### [requirements.txt](./requirements.txt)

## 🔧 Cấu hình

### Cấu hình camera

- **cameras**: là cấu hình của các camera trong hệ thống
    - **source**: là đường dẫn đến camera hoặc video, có thể là `0`, `1`, `2` ... cho các camera mặc định hoặc đường dẫn
      đến file video
    - **frame_width**:
    - **frame_height**:
    - **fps**:
- **assets**: là cấu hình các tài nguyên sử dụng trong hệ thống
    - **audio_alert** : là đường dẫn đến file âm thanh cảnh báo, ví dụ `./assets/alert.mp3`
- **drowsy_image_path**: là đường dẫn đến thư mục lưu hình ảnh cảnh báo buồn ngủ, ví dụ `./drowsy_images`
- **model_path**: là đường dẫn đến file model YOLOv11, ví dụ `core/best.pt`

```json
{
  "assets": {
    "audio_alert": "assets/alert.mp3"
  },
  "drowsy_image_path": "drowsy_images",
  "model_path": "core/best.pt",
  "camera": {
    "source": 0,
    "frame_width": 640,
    "frame_height": 480,
    "fps": 30
  }
}
```

[//]: # (## 📊 Tính năng 1)

[//]: # ()

[//]: # (- **Nhận diện nhiều khuôn mặt**: Có thể nhận diện đồng thời nhiều sinh viên)

[//]: # (- **Chống gian lận**: Phát hiện ảnh giả, video replay &#40;đang tích hợp&#41;)

## 🎯 Cách sử dụng

### Khởi chạy ứng dụng

```bash
python main1.py
```


[//]: # ()

[//]: # (### 3. Chức năng 2)

[//]: # ()

[//]: # (1. pass)

[//]: # (2. pass)

[//]: # (3. pass)

[//]: # ()

[//]: # (### 4. Chức năng 3)

[//]: # ()

[//]: # (1. pass)

[//]: # (2. pass)

[//]: # (3. pass)

## 📁 Cấu trúc project

```
comming soon
```


[//]: # (## 📊 Tính năng 1)

[//]: # ()

[//]: # (- **Nhận diện nhiều khuôn mặt**: Có thể nhận diện đồng thời nhiều sinh viên)

[//]: # (- **Chống gian lận**: Phát hiện ảnh giả, video replay &#40;đang tích hợp&#41;)

## 🐛 Troubleshooting

[//]: # (### Lỗi camera không hoạt động hoặc nguồn video không mở được)

[//]: # ()
[//]: # (```bash )

[//]: # (# Kiểm tra camera)

[//]: # (python -c "import cv2; print&#40;cv2.VideoCapture&#40;0&#41;.isOpened&#40;&#41;&#41;")

[//]: # (```)

[//]: # ()
[//]: # (```bash )

[//]: # (# Kiểm tra video)

[//]: # (python -c "import cv2; print&#40;cv2.VideoCapture&#40;\"video//videotest.mp4\"&#41;.isOpened&#40;&#41;&#41;" #thay bằng đường dẫn video của bạn")

[//]: # (```)

[//]: # (### Lỗi cài đặt dlib)

[//]: # ()
[//]: # (```bash)

[//]: # ()
[//]: # (```)

### Lỗi nhận diện kém

- Kiểm tra ánh sáng

[//]: # (- Điều chỉnh confidence_threshold)

## 👥 Tác giả

- **TranDoManhDuy** - *Developer* - [GitHub](https://github.com/TranDoManhDuy)
- **nyvantran** - *Developer* - [GitHub](https://github.com/nyvantran)
- **HieuITMHG** - *Developer* - [GitHub](https://github.com/HieuITMHG);

---

⭐ **Nếu project này hữu ích, hãy cho một star nhé!** ⭐