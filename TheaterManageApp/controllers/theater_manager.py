import json
import os
from filelock import FileLock

class TheaterManager:
    def __init__(self, json_file_path="data/theaters.json"):
        self.json_file_path = json_file_path
        self.theaters = []
        self._observers = []
        
        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
        
        # Tải dữ liệu ngay khi khởi tạo
        self.load_theaters()

        # [TỰ ĐỘNG KHỞI TẠO] Nếu chưa có rạp nào -> Tạo rạp mặc định
        # Giúp tránh lỗi không hiển thị được sơ đồ ghế
        if not self.theaters:
            print("[TheaterManager] Danh sách rạp trống. Đang tạo rạp mặc định...")
            self.create_default_theater()

    def register_observer(self, callback):
        """Đăng ký hàm callback để nhận thông báo thay đổi"""
        self._observers.append(callback)

    def notify_observers(self, message):
        """Gửi thông báo cho các observer"""
        for callback in self._observers:
            try:
                callback(message)
            except Exception:
                pass

    def load_theaters(self):
        """
        Tải danh sách rạp từ file JSON.
        Hỗ trợ cả 2 định dạng: Dictionary {"theaters": [...]} và List [...]
        """
        self.theaters = []
        if os.path.exists(self.json_file_path):
            try:
                # Kiểm tra file rỗng
                if os.path.getsize(self.json_file_path) == 0:
                    return

                with FileLock(f"{self.json_file_path}.lock", timeout=2):
                    with open(self.json_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        # --- LOGIC QUAN TRỌNG (CÁCH 1) ---
                        if isinstance(data, dict) and "theaters" in data:
                            # Trường hợp file json có dạng {"theaters": [...]}
                            self.theaters = data["theaters"]
                        elif isinstance(data, list):
                            # Trường hợp file json chỉ là danh sách [...]
                            self.theaters = data
                        else:
                            # Định dạng lạ -> Reset
                            self.theaters = []
                        # ---------------------------------
                        
            except Exception as e:
                print(f"[TheaterManager] Lỗi tải file: {e}")
                self.theaters = []
        else:
            self.theaters = []

    def save_theaters(self):
        """Lưu danh sách rạp vào file JSON (sẽ lưu dưới dạng List chuẩn)"""
        try:
            with FileLock(f"{self.json_file_path}.lock"):
                with open(self.json_file_path, "w", encoding="utf-8") as f:
                    # Lưu trực tiếp danh sách để đơn giản hóa cấu trúc cho lần sau
                    json.dump(self.theaters, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[TheaterManager] Lỗi lưu file: {e}")

    def create_default_theater(self):
        """Hàm tạo rạp mẫu nếu hệ thống chưa có dữ liệu"""
        default_theaters = [
            {
                "theater_id": "THEATER001",
                "name": "Phòng 1 (Standard)",
                "capacity": 154,
                "status": "Hoạt động",
                "location": "Tầng 3"
            },
            {
                "theater_id": "THEATER002",
                "name": "Phòng 2 (VIP)",
                "capacity": 154,
                "status": "Hoạt động",
                "location": "Tầng 3"
            }
        ]
        self.theaters.extend(default_theaters)
        self.save_theaters()
        print(f"[TheaterManager] Đã khởi tạo {len(default_theaters)} rạp mẫu.")

    def get_all_theaters(self):
        """Lấy tất cả rạp (luôn reload để đảm bảo dữ liệu mới nhất)"""
        self.load_theaters()
        return self.theaters

    def get_theater_by_id(self, theater_id):
        """Tìm rạp theo ID"""
        self.load_theaters()
        for t in self.theaters:
            if str(t.get("theater_id")) == str(theater_id):
                return t
        return None

    def add_theater(self, theater_data, user_info=None):
        """Thêm rạp mới"""
        self.load_theaters()
        
        # Validate dữ liệu đầu vào
        t_id = theater_data.get("theater_id")
        t_name = theater_data.get("name")
        
        if not t_id or not t_name:
            return "Error: ID and Name are required."

        # Kiểm tra trùng ID
        if any(str(t['theater_id']) == str(t_id) for t in self.theaters):
            return "Error: Theater ID already exists."
        
        # Kiểm tra trùng Tên
        if any(t['name'].lower() == t_name.lower() for t in self.theaters):
            return "Error: Theater Name already exists."

        # Thêm mới và lưu
        self.theaters.append(theater_data)
        self.save_theaters()
        
        self.notify_observers(f"Admin đã thêm phòng chiếu mới: {t_name}")
        return "Added successfully"