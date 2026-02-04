import cv2
import glob
import os

# Gom frame hình thành video
frame_folder = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025\drowsy_images\drowsy_20251101_161324"
output_video = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025\services\output_video.mp4"
fps = 30 

image_files = sorted(glob.glob(os.path.join(frame_folder, "*.jpg")))  # hoặc *.png

if not image_files:
    raise ValueError("Không tìm thấy frame nào trong thư mục.")

frame = cv2.imread(image_files[0])
height, width = frame.shape[:2]

fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec MP4
out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

for img_file in image_files:
    frame = cv2.imread(img_file)
    if frame.shape[:2] != (height, width):
        frame = cv2.resize(frame, (width, height))
    out.write(frame)

out.release()
print(f"Video đã được lưu tại: {output_video}")