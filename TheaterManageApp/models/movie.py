import uuid
import re
from datetime import datetime

# --- ĐÃ SỬA TÊN THAM SỐ THÀNH 'format' ĐỂ SỬA LỖI 2 ---
def validate_date(date_str, format="%d-%m-%Y"):
    """
    Chuẩn hóa chuỗi ngày tháng.
    """
    if not date_str:
        return None
    
    if isinstance(date_str, datetime):
        return date_str.strftime(format)

    # Các định dạng input thường gặp
    input_formats = ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"]
    
    for fmt in input_formats:
        try:
            parsed_date = datetime.strptime(str(date_str), fmt)
            # Trả về theo format yêu cầu
            return parsed_date.strftime(format)
        except ValueError:
            continue
            
    # Fallback: Trả về chuỗi gốc nếu có vẻ đúng (tránh crash)
    if isinstance(date_str, str) and len(date_str) >= 10:
        return date_str[:10]
    
    # Hoặc trả về ngày hiện tại để an toàn
    return datetime.now().strftime(format)

class Movie:
    def __init__(self, ma_phim=None, title=None, description=None, year=None, 
                 genre=None, duration=None, poster_path=None, rating=None, 
                 age_rating=None, release_date=None, cast=None, director=None, 
                 showtimes=None, status=None, created_at=None):
        
        self.ma_phim = str(ma_phim) if ma_phim else str(uuid.uuid4())
        self.title = title or "Unknown"
        self.description = description or "Đang cập nhật..."
        self.year = str(year)[:4] if year else datetime.now().strftime("%Y")
        self.genre = genre or "N/A"
        
        try: self.duration = int(duration)
        except: self.duration = 120
            
        self.poster_path = poster_path or ""
        
        try: self.rating = float(rating) if rating is not None else 0.0
        except: self.rating = 0.0
            
        self.age_rating = age_rating
        self.release_date = validate_date(release_date)
            
        self.cast = cast if isinstance(cast, list) else []
        self.director = director or "N/A"
        self.showtimes = showtimes if isinstance(showtimes, list) else []
        self.status = status or "Sắp chiếu"
        self.created_at = created_at or datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    def to_dict(self):
        return {
            "ma_phim": self.ma_phim,
            "title": self.title,
            "description": self.description,
            "year": self.year,
            "genre": self.genre,
            "duration": self.duration,
            "poster_path": self.poster_path,
            "rating": self.rating,
            "age_rating": self.age_rating,
            "release_date": self.release_date,
            "cast": self.cast,
            "director": self.director,
            "showtimes": self.showtimes,
            "status": self.status,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            ma_phim=data.get("ma_phim"),
            title=data.get("title"),
            description=data.get("description"),
            year=data.get("year"),
            genre=data.get("genre"),
            duration=data.get("duration"),
            poster_path=data.get("poster_path"),
            rating=data.get("rating"),
            age_rating=data.get("age_rating"),
            release_date=data.get("release_date"),
            cast=data.get("cast"),
            director=data.get("director"),
            showtimes=data.get("showtimes"),
            status=data.get("status"),
            created_at=data.get("created_at")
        )

    def validate(self):
        if not self.ma_phim: raise ValueError("Mã phim trống")
        if not self.title: raise ValueError("Tên phim trống")