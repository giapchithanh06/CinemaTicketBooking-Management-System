import json
import os
import threading
from datetime import datetime
from filelock import FileLock
from models.movie import Movie
from services.api_crawler import MovieCrawler

class MovieManager:
    def __init__(self, api_key, json_file_path="data/movies.json"):
        self.crawler = MovieCrawler(api_key)
        self.json_file_path = json_file_path
        self.now_showing = []
        self.upcoming = []
        self._observers = []
        
        # Tạo thư mục data nếu chưa có
        os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)

        # 1. Tải dữ liệu cũ từ file JSON trước (để hiện ngay lập tức)
        print("--- Đang tải dữ liệu từ JSON nội bộ ---")
        self.load_local_data()
        
        # 2. Chạy luồng cập nhật API ngầm (Không làm đơ giao diện)
        print("--- Đang khởi động luồng cập nhật API ---")
        update_thread = threading.Thread(target=self.update_from_api, daemon=True)
        update_thread.start()

    def register_observer(self, callback):
        self._observers.append(callback)

    def notify_observers(self, message):
        for callback in self._observers:
            try:
                callback(message)
            except Exception:
                pass

    def _parse_date(self, date_str):
        if not date_str: return datetime.min
        try:
            return datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return datetime.min

    def _classify_movie(self, movie):
        """
        Phân loại phim:
        - QUAN TRỌNG: Nếu không có ảnh hoặc file ảnh không tồn tại -> BỎ QUA LUÔN.
        """
        # 1. KIỂM TRA ẢNH (Thêm đoạn này vào)
        # Nếu đường dẫn rỗng HOẶC file không tồn tại trên ổ cứng
        if not movie.poster_path or not os.path.exists(movie.poster_path):
            return  # <--- Lệnh này sẽ xóa phim "Ai Thương Ai Mến" khỏi danh sách
        
        # 2. Xử lý thời gian (Giữ nguyên logic cũ)
        if not movie.release_date:
            return

        release_date = self._parse_date(movie.release_date)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Logic phân loại
        if release_date > today:
            self.upcoming.append(movie)
        else:
            delta = today - release_date
            if delta.days < 35: # Giới hạn 5 tuần
                self.now_showing.append(movie)

    def load_local_data(self):
        """Đọc file JSON để hiển thị dữ liệu cũ ngay lập tức"""
        self.now_showing = []
        self.upcoming = []
        
        if os.path.exists(self.json_file_path):
            try:
                with FileLock(f"{self.json_file_path}.lock", timeout=2):
                    with open(self.json_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        # Gộp tất cả phim lại để phân loại lại từ đầu
                        all_movies_data = data.get("now_showing", []) + data.get("upcoming", [])
                        unique_movies = {}
                        
                        for m_data in all_movies_data:
                            # Chuyển dict -> object Movie
                            m = Movie.from_dict(m_data)
                            unique_movies[m.title] = m
                        
                        # Phân loại lại
                        for movie in unique_movies.values():
                            self._classify_movie(movie)
                            
                print(f"-> Đã load từ JSON: {len(self.now_showing)} đang chiếu, {len(self.upcoming)} sắp chiếu.")
            except Exception as e:
                print(f"Lỗi đọc file JSON: {e}")
        else:
            print("-> Chưa có file JSON, chờ API cập nhật...")

    def update_from_api(self):
        """Hàm chạy ngầm để lấy dữ liệu mới từ API"""
        try:
            print("-> Bắt đầu gọi API...")
            api_movies = []
            
            # Gọi API (Lấy nhiều trang)
            now_showing_data = self.crawler.get_now_showing_movies(pages=2)
            upcoming_data = self.crawler.get_upcoming_movies(pages=2)
            
            api_movies.extend(now_showing_data)
            api_movies.extend(upcoming_data)
            
            print(f"-> API trả về tổng cộng: {len(api_movies)} bộ phim thô.")

            if not api_movies:
                print("CẢNH BÁO: API không trả về phim nào. Kiểm tra API Key hoặc Mạng.")
                return

            has_change = False
            # Dùng Set để kiểm tra trùng tiêu đề nhanh hơn
            existing_titles = {m.title for m in self.now_showing + self.upcoming}

            for d in api_movies:
                title = d.get("title")
                if not title: continue
                
                # Nếu phim đã có rồi thì bỏ qua (hoặc cập nhật nếu muốn)
                if title in existing_titles: continue

                # Tải Poster
                poster_raw = d.get("poster_path")
                local_poster_path = None
                if poster_raw:
                    local_poster_path = self.crawler.download_poster(poster_raw, d["id"])
                
                poster_raw = d.get("poster_path")
                if not poster_raw: 
                    continue # API không có link ảnh -> Bỏ qua

                local_poster_path = self.crawler.download_poster(poster_raw, d["id"])
            
                # [THÊM ĐOẠN NÀY] Nếu tải ảnh thất bại -> Bỏ qua phim này luôn
                if not local_poster_path: 
                    continue
                # Tạo object Movie
                m = Movie(
                    title=title,
                    description=d.get("overview", "Chưa có mô tả"),
                    year=d.get("release_date", "")[:4],
                    poster_path=local_poster_path, # Có thể là None nếu lỗi tải ảnh
                    rating=d.get("vote_average", 0),
                    duration=120, # Mặc định tạm
                    release_date=d.get("release_date")
                )
                
                # Lấy chi tiết (thời lượng, thể loại)
                # Lưu ý: Gọi chi tiết tốn thời gian, có thể làm chậm
                details = self.crawler.get_movie_details(d["id"])
                if details:
                    m.duration = details.get("runtime", 120)
                    genres = details.get("genres", [])
                    if genres:
                        m.genre = ", ".join([g["name"] for g in genres])

                # Phân loại và thêm vào list
                self._classify_movie(m)
                
                # Nếu phim được thêm vào list thành công
                if m in self.now_showing or m in self.upcoming:
                    existing_titles.add(title)
                    has_change = True
                    print(f"   + Mới: {title}")

            if has_change:
                print("-> Có dữ liệu mới, đang lưu vào JSON...")
                self.save_movies()
                self.notify_observers("Dữ liệu phim mới đã được cập nhật!")
            else:
                print("-> Dữ liệu API trùng khớp với hiện tại, không cần cập nhật.")

        except Exception as e:
            print(f"Lỗi cập nhật API: {e}")

    def save_movies(self):
        data = {
            "now_showing": [m.to_dict() for m in self.now_showing],
            "upcoming": [m.to_dict() for m in self.upcoming]
        }
        try:
            with FileLock(f"{self.json_file_path}.lock"):
                with open(self.json_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            print("-> Đã lưu file movies.json thành công.")
        except Exception as e:
            print(f"Lỗi lưu file: {e}")

    def get_all_movies(self):
        return {
            "now_showing": [m.to_dict() for m in self.now_showing],
            "upcoming": [m.to_dict() for m in self.upcoming]
        }
        
    def get_movie_by_id(self, ma_phim):
        for movie in self.now_showing + self.upcoming:
            if str(movie.ma_phim) == str(ma_phim): return movie
        return None

    def get_now_showing(self): return self.now_showing
    def get_upcoming(self): return self.upcoming