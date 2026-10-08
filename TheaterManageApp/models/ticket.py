import uuid
from datetime import datetime
import re

def validate_date(date_str, format="%d-%m-%Y"):
    """Chuẩn hóa ngày về định dạng DD-MM-YYYY."""
    if not date_str: return None
    if isinstance(date_str, datetime): return date_str.strftime(format)
    
    formats = ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt).strftime(format)
        except ValueError:
            continue
    raise ValueError(f"Ngày không hợp lệ: {date_str}. Yêu cầu: DD-MM-YYYY")

def validate_show_time(show_time):
    if not show_time or not re.match(r"\d{2}:\d{2}", str(show_time)):
        raise ValueError("Giờ chiếu phải có định dạng HH:MM")
    return str(show_time)

class Ticket:
    def __init__(self, ticket_id, username, movie_title, show_time, seats, date=None, room=None, name=None, phone=None, email=None, payment_method=None, price=0):
        self.ticket_id = str(ticket_id) if ticket_id else str(uuid.uuid4())
        self.username = username
        self.movie_title = movie_title
        self.show_time = validate_show_time(show_time)
        
        # Luôn lưu seats dưới dạng List để dễ xử lý logic
        if isinstance(seats, str):
            self.seats = [s.strip() for s in seats.split(",")]
        elif isinstance(seats, list):
            self.seats = seats
        else:
            self.seats = []
            
        self.date = validate_date(date) if date else datetime.now().strftime("%d-%m-%Y")
        self.room = room
        self.name = name
        self.phone = phone
        self.email = email
        self.payment_method = payment_method
        self.price = float(price) if price is not None else 0.0

    def to_dict(self):
        return {
            "ticket_id": self.ticket_id,
            "username": self.username,
            "movie_title": self.movie_title,
            "show_time": self.show_time,
            "seats": self.seats, # Lưu List vào JSON
            "date": self.date,
            "room": self.room,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "payment_method": self.payment_method,
            "price": self.price
        }

    @staticmethod
    def from_dict(data):
        return Ticket(
            ticket_id=data.get('ticket_id'),
            username=data.get('username', ''),
            movie_title=data.get('movie_title', ''),
            show_time=data.get('show_time', '00:00'),
            seats=data.get('seats', []),
            date=data.get('date'),
            room=data.get('room'),
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            payment_method=data.get('payment_method'),
            price=data.get('price', 0)
        )