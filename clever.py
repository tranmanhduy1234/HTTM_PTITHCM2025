# import os
# from services.user_service import UserService
# import shutil

# def clear_folder_fast(path):
#     if os.path.exists(path):
#         shutil.rmtree(path)  # Xóa sạch thư mục và mọi thứ bên trong
#     os.makedirs(path)        # Tạo lại thư mục trống

# # Đường dẫn cho tập train
# tmp_dir_dataset_Drowsy = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025\tmp_dataset\train\Drowsy"
# tmp_dir_dataset_Natural = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025\tmp_dataset\train\Natural"
# # Đường dẫn cho tập test
# tmp_dir_dataset_Drowsy_test = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025\tmp_dataset\test\Drowsy"
# tmp_dir_dataset_Natural_test = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025\tmp_dataset\test\Natural"

# # Xóa sạch sẽ folder trước khi training
# clear_folder_fast(tmp_dir_dataset_Drowsy)
# clear_folder_fast(tmp_dir_dataset_Natural)
# clear_folder_fast(tmp_dir_dataset_Drowsy_test)
# clear_folder_fast(tmp_dir_dataset_Natural_test)

# source_training = "D:\\ptithcm\\HTTM\\HTTM_PTITHCM2025\\drowsy_images"
# def training(userID=1):
#     path_folderTrainPersonal = ""
#     Drowsy = []
#     Natural = []
#     for folder in os.listdir(source_training):
#         if not os.path.isfile(os.path.join(source_training, folder)): 
#             # ta có userID, và folder image session mới nhất của người đó.
#             path_folderTrainPersonal = os.path.join(source_training, folder)
#     print(path_folderTrainPersonal)
#     if path_folderTrainPersonal != "":
#         for image_path in os.listdir(path_folderTrainPersonal):
#             if image_path.endswith("Drowsy.jpg"): Drowsy.append(os.path.join(path_folderTrainPersonal, image_path))
#             if image_path.endswith("Natural.jpg"): Natural.append(os.path.join(path_folderTrainPersonal, image_path))
#         Drowsy = Drowsy[:min(len(Drowsy), len(Natural))]
#         Natural = Natural[:min(len(Drowsy), len(Natural))]
#         print(len(Drowsy), len(Natural))
        
#     # TẠO TẬP TRAIN
#     # Đã có 2 danh sách các đường dẫn ảnh 
#     for img_path_drowsy in Drowsy[0:int(len(Drowsy) * 0.8)]:
#         fileName = os.path.basename(img_path_drowsy)
#         dest_path = os.path.join(tmp_dir_dataset_Drowsy, fileName)
#         shutil.copy(img_path_drowsy, dest_path)
#     for img_path_natural in Natural[0:int(len(Natural) * 0.8)]:
#         fileName = os.path.basename(img_path_natural)
#         dest_path = os.path.join(tmp_dir_dataset_Natural, fileName)
#         shutil.copy(img_path_natural, dest_path)
#     # Ta đã có 2 folder
    
#     # TẠO TẬP TEST
#     for img_path_drowsy in Drowsy[int(len(Drowsy) * 0.8):]:
#         fileName = os.path.basename(img_path_drowsy)
#         dest_path = os.path.join(tmp_dir_dataset_Drowsy_test, fileName)
#         shutil.copy(img_path_drowsy, dest_path)
#     for img_path_natural in Natural[int(len(Natural) * 0.8):]:
#         fileName = os.path.basename(img_path_natural)
#         dest_path = os.path.join(tmp_dir_dataset_Natural_test, fileName)
#         shutil.copy(img_path_natural, dest_path)
        
#     exit(0)
#     # Tiến hành train model
#     # kiểm tra model của user đã tồn tại hay chưa, dẫn tới model cũ
#     from ultralytics import YOLO
#     path_model_old = fr"D:\ptithcm\HTTM\HTTM_PTITHCM2025\model_{userID}.pt"
#     if os.path.exists(path_model_old):
#         model = YOLO(path_model_old)
#     else:
#         model = YOLO("yolo11n-cls.pt")
#     results = model.train(data=r"D:\ptithcm\HTTM\HTTM_PTITHCM2025\tmp_dataset", epochs=10, imgsz=640)
#     # kết quả sẽ được trả về 1 folder mới.
#     print(results.save_dir)
    
# if __name__=="__main__":
#     userID = "1"
#     import db.db as database 
#     conn = database.get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         SELECT * FROM Session
#         WHERE userID = ?
#     """, userID)
#     rows = cursor.fetchall()
#     # 0 là Session ID, 1 là User ID
#     rows = sorted([(r[0], r[1]) for r in rows], key=lambda x: x[0], reverse=True)
#     training(userID=rows[0][0])

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import db.db as database
from ultralytics import YOLO

class ModelTrainer:
    """Lớp quản lý việc train model phát hiện buồn ngủ"""
    
    def __init__(self, base_dir: str = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025"):
        self.base_dir = Path(base_dir)
        self.source_training = self.base_dir / "drowsy_images"
        self.tmp_dataset = self.base_dir / "tmp_dataset"
        
        # Định nghĩa các đường dẫn
        self.train_drowsy = self.tmp_dataset / "train" / "Drowsy"
        self.train_natural = self.tmp_dataset / "train" / "Natural"
        self.test_drowsy = self.tmp_dataset / "test" / "Drowsy"
        self.test_natural = self.tmp_dataset / "test" / "Natural"
        
        self.train_test_split = 0.8
        
    def clear_folder(self, path: Path) -> None:
        """Xóa và tạo lại thư mục rỗng"""
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        
    def prepare_directories(self) -> None:
        """Chuẩn bị các thư mục cần thiết"""
        print("Đang chuẩn bị thư mục...")
        for directory in [self.train_drowsy, self.train_natural, 
                         self.test_drowsy, self.test_natural]:
            self.clear_folder(directory)
        print("Hoàn tất chuẩn bị thư mục")
        
    def get_latest_session_folder(self, session_id) -> Optional[Path]:
        if not self.source_training.exists():
            print(f"Thư mục {self.source_training} không tồn tại")
            return None
        folders = [
            f for f in os.listdir(self.source_training)
            if not os.path.isfile(f) and f.endswith(str(session_id))
        ]
        if not folders:
            print("Không tìm thấy folder nào trong thư mục training")
            return None
        latest_folder = folders
        print(f"Folder training mới nhất: {latest_folder}")
        return latest_folder
        
    def collect_images(self, folder_paths: Path) -> Tuple[List[Path], List[Path]]:
        """Thu thập các ảnh Drowsy và Natural từ folder"""
        drowsy_images = []
        natural_images = []
        for folder_path in folder_paths:
            if not folder_path or not os.path.exists(os.path.join(self.source_training, folder_path)):
                return drowsy_images, natural_images
            
            folder_path_full = os.path.join(self.source_training, folder_path)
            for image_file in os.listdir(folder_path_full):
                if not image_file.endswith(".jpg"):
                    continue
                    
                if "Drowsy" in image_file:
                    drowsy_images.append(os.path.join(folder_path_full, image_file))
                elif "Natural" in image_file:
                    natural_images.append(os.path.join(folder_path_full, image_file))
                
        return drowsy_images, natural_images
        
    def balance_dataset(self, drowsy: List[Path], natural: List[Path]) -> Tuple[List[Path], List[Path]]:
        """Cân bằng số lượng ảnh giữa 2 class"""
        min_length = min(len(drowsy), len(natural))
        return drowsy[:min_length], natural[:min_length]
        
    def split_and_copy_images(self, drowsy: List[Path], natural: List[Path]) -> None:
        """Chia dataset thành train/test và copy ảnh"""
        split_idx = int(len(drowsy) * self.train_test_split)
        
        print(f"Đang copy {split_idx} ảnh train cho mỗi class...")
        print(f"Đang copy {len(drowsy) - split_idx} ảnh test cho mỗi class...")
        
        # Copy train set
        self._copy_images(drowsy[:split_idx], self.train_drowsy)
        self._copy_images(natural[:split_idx], self.train_natural)
        
        # Copy test set
        self._copy_images(drowsy[split_idx:], self.test_drowsy)
        self._copy_images(natural[split_idx:], self.test_natural)
        
        print("Hoàn tất copy ảnh")
        
    def _copy_images(self, image_list: List[Path], dest_dir: Path) -> None:
        """Copy danh sách ảnh vào thư mục đích"""
        for img_path in image_list:
            dest_path = dest_dir / os.path.basename(img_path)
            shutil.copy2(img_path, dest_path)
            
    def get_model_path(self, user_id: int) -> Path:
        """Lấy đường dẫn model của user"""
        return self.base_dir / "model"/f"model_{user_id}.pt"
        
    def train_model(self, user_id: int, epochs: int = 1, imgsz: int = 640) -> str:
        """Train model YOLO"""
        print(f"\nBắt đầu train model cho user {user_id}...")
        
        model_path = self.get_model_path(user_id)
        # Load model cũ nếu có, không thì load pretrained
        if model_path.exists():
            print(f"Sử dụng model cũ: {model_path}")
            model = YOLO(str(model_path))
        else:
            print("Sử dụng model pretrained: yolo11n-cls.pt")
            model = YOLO("yolo11n-cls.pt")
            
        # Train model
        results = model.train(
            data=str(self.tmp_dataset),
            epochs=epochs,
            imgsz=imgsz,
            verbose=True
        )
        
        print(f"\nKết quả train được lưu tại: {results.save_dir}")
        save_dir = results.save_dir
        return save_dir
        
    def run_training_pipeline(self, session_id: int, user_id: int) -> None:
        """Chạy toàn bộ pipeline training"""
        try:
            # 1. Chuẩn bị thư mục
            self.prepare_directories()
            
            # 2. Lấy folder training mới nhất
            training_folders = self.get_latest_session_folder(session_id)
            if not training_folders:
                print("Không tìm thấy dữ liệu training")
                return
            
            # 3. Thu thập ảnh, 2 arr chứa đường dẫn các ảnh, đường dẫn đầy đủ.
            drowsy, natural = self.collect_images(training_folders)
            print(f"Tìm thấy: {len(drowsy)} ảnh Drowsy, {len(natural)} ảnh Natural")
            
            if not drowsy or not natural:
                print("Không đủ dữ liệu để training")
                return
                
            # 4. Cân bằng dataset
            drowsy, natural = self.balance_dataset(drowsy, natural)
            print(f"Dataset sau khi cân bằng: {len(drowsy)} ảnh mỗi class")
            
            # 5. Chia và copy ảnh
            self.split_and_copy_images(drowsy, natural)
            
            # 6. Train model
            save_dir = self.train_model(user_id)
            
            print("\n✓ Hoàn tất quá trình training!")
            print(f"\n✓ Kết quả lưu tại {save_dir}")
            
            path_new_model = save_dir / "weights" / "best.pt"
            if os.path.exists(path_new_model):
                print(f"\n✓ Tìm thấy đường dẫn file kết quả model tại: {path_new_model}")
                path_old_model = self.get_model_path(user_id)
                
                try:
                    os.remove(path_old_model)
                except Exception as e:
                    print(e)
                    print(f"\n Model đầu tiên của user mang ID: {user_id}")
                shutil.copy(path_new_model, path_old_model)
            else:
                print("Lỗi đường dẫn file model kết quả")
            
        except Exception as e:
            print(f"✗ Lỗi trong quá trình training: {str(e)}")
            raise

def get_latest_session_id(user_id: str) -> Optional[int]:
    """Lấy session ID mới nhất của user từ database"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ID, userID 
            FROM Session
            WHERE userID = ?
            ORDER BY ID DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return row[0] if row else None
        
    except Exception as e:
        print(f"Lỗi khi truy vấn database: {str(e)}")
        return None

def main(user_id):
    # Lấy session ID mới nhất (nếu cần)
    session_id = get_latest_session_id(user_id)
    if session_id:
        print(f"Session ID mới nhất: {session_id}")
    base_dir = r"D:\ptithcm\HTTM\HTTM_PTITHCM2025"
    # Khởi tạo trainer và chạy
    trainer = ModelTrainer(base_dir=base_dir)
    trainer.run_training_pipeline(int(session_id), user_id=int(user_id))