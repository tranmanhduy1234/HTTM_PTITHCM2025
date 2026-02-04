import os
import cv2
from repository.frame_repo import get_frames_by_video


class VideoManager:
    def __init__(self):
        pass
    def get_drowsy_video(self, video_id: int):
        """Lấy đối tượng VideoCapture cho video drowsy cụ thể."""
        frames = get_frames_by_video(video_id)
        image_paths = [frame["imageURL"] for frame in frames]

        folder_path = image_paths[0].split("/")[:-1]
        video_path = os.path.join(*folder_path, f"drowsy_video_{video_id}.mp4")
        
        if not os.path.exists(video_path):
            # Tạo video từ các frame
            first_frame = cv2.imread(image_paths[0])
            height, width, layers = first_frame.shape
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video = cv2.VideoWriter(
                video_path,
                fourcc,
                30.0, (width, height))
            for image_path in image_paths:
                frame = cv2.imread(image_path)
                video.write(frame)
            video.release()
            print("done creating video:", video_path)

        return video_path


# def main():
#     video_manager = VideoManager()
#     print(video_manager.get_drowsy_video(video_id=114))
#
#
# if __name__ == "__main__":
#     main()
