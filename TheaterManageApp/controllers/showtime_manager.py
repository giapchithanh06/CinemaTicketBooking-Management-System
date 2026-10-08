import json
import os
import uuid
import random 
from datetime import datetime, timedelta
import re
from filelock import FileLock

def validate_show_time(show_time):
    if not show_time or not re.match(r"\d{2}:\d{2}", show_time):
        return "00:00"
    return show_time

class Showtime:
    def __init__(self, showtime_id, movie_title, theater_id, show_time, date):
        self.showtime_id = str(showtime_id) if showtime_id else str(uuid.uuid4())
        self.movie_title = movie_title or "Unknown"
        self.theater_id = theater_id or "N/A"
        self.show_time = validate_show_time(show_time)
        self.date = date 
        self.created_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    def to_dict(self): return self.__dict__.copy()
    
    @staticmethod
    def from_dict(data):
        return Showtime(data.get("showtime_id"), data.get("movie_title"), 
                        data.get("theater_id"), data.get("show_time"), data.get("date"))

class ShowtimeManager:
    def __init__(self, json_file_path="data/showtimes.json"):
        self.json_file_path = json_file_path
        self.lock_path = f"{self.json_file_path}.lock"
        self.showtimes = []
        self._observers = []
        self.load_showtimes()
        
        # Tự động tạo lịch chiếu thông minh nếu chưa có
        self.generate_smart_schedule()

    def register_observer(self, cb): self._observers.append(cb)
    def notify_observers(self, msg):
        for cb in self._observers: 
            try: cb(msg)
            except: pass

    def load_showtimes(self):
        self.showtimes = []
        if os.path.exists(self.json_file_path):
            try:
                with FileLock(self.lock_path, timeout=5):
                    with open(self.json_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.showtimes = [Showtime.from_dict(i) for i in data.get("showtimes", [])]
            except: pass
        return self.showtimes

    def save_showtimes(self):
        try:
            os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
            with FileLock(self.lock_path, timeout=5):
                with open(self.json_file_path, 'w', encoding='utf-8') as f:
                    json.dump({"showtimes": [s.to_dict() for s in self.showtimes]}, f, indent=4, ensure_ascii=False)
        except: pass

    def get_all_showtimes(self):
        self.load_showtimes()
        return [s.to_dict() for s in self.showtimes]

    def add_showtime(self, data, user):
        if user.get("type") != "Admin": return "Từ chối"
        s = Showtime(None, data["movie_title"], data["theater_id"], data["show_time"], data["date"])
        self.showtimes.append(s)
        self.save_showtimes()
        return "Added"

    # --- LOGIC TẠO LỊCH CHIẾU (06:00 -> 23:00, CÁCH NHAU 1H-2H) ---
    def generate_smart_schedule(self):
        today_str = datetime.now().strftime("%d-%m-%Y")
        
        # Nếu hôm nay đã có lịch thì không tạo lại
        if any(s.date == today_str for s in self.showtimes):
            return

        print("Đang tạo lịch chiếu tự động (06h-23h, giãn cách 1h-2h)...")
        try:
            # 1. Lấy phim Đang Chiếu
            movies = []
            if os.path.exists("data/movies.json"):
                with open("data/movies.json", 'r', encoding='utf-8') as f:
                    md = json.load(f)
                    movies = [m["title"] for m in md.get("now_showing", [])]
            
            # 2. Lấy phòng rạp
            theaters = []
            if os.path.exists("data/theaters.json"):
                with open("data/theaters.json", 'r', encoding='utf-8') as f:
                    td = json.load(f)
                    theaters = [t["theater_id"] for t in td.get("theaters", []) if t["status"] == "Hoạt động"]
            
            if not movies: return 
            if not theaters: theaters = ["1", "2", "3", "4"] 

            new_shows = []
            
            # 3. Tạo lịch cho 7 ngày tới
            for day_offset in range(7):
                current_date = (datetime.now() + timedelta(days=day_offset)).strftime("%d-%m-%Y")
                
                # Tạo một danh sách giờ chiếu động cho ngày hôm nay
                # Bắt đầu 06:00, kết thúc trước 23:00
                # Bước nhảy ngẫu nhiên từ 60 đến 120 phút (1h - 2h)
                daily_time_pool = []
                current_min = 6 * 60 # 06:00 quy ra phút
                end_min = 23 * 60 + 30 # 23:30 giới hạn
                
                while current_min < end_min:
                    h = current_min // 60
                    m = current_min % 60
                    # Làm tròn phút cho đẹp (00, 15, 30, 45)
                    m = round(m / 15) * 15
                    if m == 60: 
                        h += 1
                        m = 0
                    
                    time_str = f"{h:02}:{m:02}"
                    daily_time_pool.append(time_str)
                    
                    # Cộng thêm ngẫu nhiên từ 60 đến 120 phút cho suất tiếp theo
                    gap = random.randint(60, 120)
                    current_min += gap

                # Phân phối phim vào các giờ này
                for movie_title in movies:
                    # Mỗi phim chọn ngẫu nhiên khoảng 3-5 suất từ pool giờ đã tạo
                    # Để đảm bảo không phim nào giống hệt phim nào
                    if len(daily_time_pool) > 3:
                        num_shows = random.randint(3, min(len(daily_time_pool), 6))
                        movie_slots = random.sample(daily_time_pool, num_shows)
                        movie_slots.sort()
                    else:
                        movie_slots = daily_time_pool

                    for slot in movie_slots:
                        # Chọn ngẫu nhiên rạp
                        tid = random.choice(theaters)
                        s = Showtime(
                            showtime_id=None,
                            movie_title=movie_title,
                            theater_id=tid,
                            show_time=slot,
                            date=current_date
                        )
                        new_shows.append(s)

            if new_shows:
                self.showtimes.extend(new_shows)
                self.save_showtimes()
                print(f"Đã tạo {len(new_shows)} suất chiếu mới.")
                
        except Exception as e:
            print(f"Lỗi tạo lịch chiếu: {e}")