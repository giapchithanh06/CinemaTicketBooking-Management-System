import uuid
import re
from datetime import datetime

def validate_date(date_str, output_format="%d-%m-%Y"):
    """
    Chuẩn hóa chuỗi ngày tháng về định dạng DD-MM-YYYY.
    Chấp nhận input là chuỗi hoặc datetime object.
    """
    if not date_str or date_str == "N/A":
        return "N/A"
    
    if isinstance(date_str, datetime):
        return date_str.strftime(output_format)

    try:
        # Thử parse các định dạng phổ biến
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime(output_format)
            except ValueError:
                continue
        # Nếu không khớp định dạng nào
        raise ValueError
    except ValueError:
        # Trả về N/A hoặc raise lỗi tùy nhu cầu, ở đây ta chấp nhận N/A để tránh crash UI
        return "N/A"

class User:
    def __init__(self, user_id, username, password, full_name, phone, email, is_logged_in=False):
        self.user_id = str(user_id) if user_id else str(uuid.uuid4())
        self.username = username or "Unknown"
        
        # Lưu ý: password ở đây là chuỗi HASH (từ DB) hoặc chuỗi rỗng.
        # Class User KHÔNG thực hiện hashing.
        self.password = password if password else ""
        
        self.full_name = full_name or "N/A"
        self.phone = phone or "N/A"
        self.email = email or "N/A"
        self.is_logged_in = bool(is_logged_in)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "password": self.password,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "is_logged_in": self.is_logged_in,
            "type": "User"
        }

    @staticmethod
    def from_dict(data):
        return User(
            user_id=data.get('user_id', data.get('id', str(uuid.uuid4()))),
            username=data.get('username', 'Unknown'),
            password=data.get('password', ''),
            full_name=data.get('full_name', 'N/A'),
            phone=data.get('phone', 'N/A'),
            email=data.get('email', 'N/A'),
            is_logged_in=data.get('is_logged_in', False)
        )

    def login(self):
        self.is_logged_in = True

    def logout(self):
        self.is_logged_in = False

    def validate(self):
        """Kiểm tra tính hợp lệ của dữ liệu User."""
        if not self.user_id:
            raise ValueError("User ID không được để trống")
        if not self.username or self.username == "Unknown":
            raise ValueError("Username không được để trống")
        if not self.email or self.email == "N/A":
            raise ValueError("Email không được để trống")
        
        # Regex Email cơ bản
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            raise ValueError("Định dạng Email không hợp lệ")
        
        # Regex Phone: Chấp nhận số, dấu cộng, dấu cách, dấu gạch ngang, ngoặc đơn
        # VD: +84 909-123-456 hoặc 0901234567
        if self.phone != "N/A":
             if not re.match(r"^[\d\+\-\s\(\)]{10,20}$", self.phone):
                raise ValueError("Định dạng số điện thoại không hợp lệ")

class Admin(User):
    def __init__(self, user_id, username, password, full_name, phone, email, 
                 birth_date, gender, address, position, is_logged_in=False):
        super().__init__(user_id, username, password, full_name, phone, email, is_logged_in)
        
        self.birth_date = validate_date(birth_date)
        self.gender = gender or "N/A"
        self.address = address or "N/A"
        self.position = position or "N/A"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "birth_date": self.birth_date,
            "gender": self.gender,
            "address": self.address,
            "position": self.position,
            "type": "Admin"
        })
        return data

    @staticmethod
    def from_dict(data):
        return Admin(
            user_id=data.get('user_id', data.get('id', str(uuid.uuid4()))),
            username=data.get('username', 'Unknown'),
            password=data.get('password', ''),
            full_name=data.get('full_name', 'N/A'),
            phone=data.get('phone', 'N/A'),
            email=data.get('email', 'N/A'),
            birth_date=data.get('birth_date', 'N/A'),
            gender=data.get('gender', 'N/A'),
            address=data.get('address', 'N/A'),
            position=data.get('position', 'N/A'),
            is_logged_in=data.get('is_logged_in', False)
        )

    def validate(self):
        super().validate()
        if not self.position or self.position == "N/A":
            raise ValueError("Admin phải có chức vụ (position)")
        
        # Kiểm tra ngày sinh nếu có
        if self.birth_date != "N/A":
             # validate_date đã chuẩn hóa về DD-MM-YYYY, ta chỉ check regex đơn giản
             if not re.match(r"\d{2}-\d{2}-\d{4}", self.birth_date):
                 raise ValueError("Ngày sinh phải có định dạng DD-MM-YYYY")
                 
        if self.gender != "N/A" and self.gender not in ["Nam", "Nữ", "Khác"]:
             # Cảnh báo nhẹ hoặc bỏ qua nếu muốn linh hoạt hơn
             pass