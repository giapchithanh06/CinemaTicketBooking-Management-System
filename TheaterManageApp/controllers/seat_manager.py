import json
import os
import uuid
from filelock import FileLock

class Seat:
    def __init__(self, seat_id, theater_id, seat_number, status="available", seat_type="Standard"):
        self.seat_id = str(seat_id) if seat_id else str(uuid.uuid4())
        self.theater_id = theater_id or "N/A"
        self.seat_number = seat_number or "N/A"
        self.status = status or "available"
        self.seat_type = seat_type or "Standard"
    
    def to_dict(self): return self.__dict__.copy()
    
    @staticmethod
    def from_dict(data):
        return Seat(
            data.get("seat_id"), data.get("theater_id"), 
            data.get("seat_number"), data.get("status"), data.get("seat_type")
        )

class SeatManager:
    def __init__(self, json_file_path="data/seats.json"):
        self.json_file_path = json_file_path
        self.lock_path = f"{self.json_file_path}.lock"
        self._observers = []

    def register_observer(self, callback): self._observers.append(callback)
    def notify_observers(self, msg):
        for cb in self._observers: 
            try: cb(msg)
            except: pass

    def _load_unsafe(self):
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [Seat.from_dict(item) for item in data.get("seats", [])]
            except: return []
        return []

    def _save_unsafe(self, seats):
        os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump({"seats": [s.to_dict() for s in seats]}, f, indent=4, ensure_ascii=False)

    def get_seats_by_theater(self, theater_id):
        with FileLock(self.lock_path, timeout=5):
            seats = self._load_unsafe()
        return [s.to_dict() for s in seats if str(s.theater_id) == str(theater_id)]

    def add_seat(self, seat_data, current_user=None):
        try:
            with FileLock(self.lock_path, timeout=5):
                seats = self._load_unsafe()
                for s in seats:
                    if str(s.theater_id) == str(seat_data.get("theater_id")) and s.seat_number == seat_data.get("seat_number"):
                        return "Ghế đã tồn tại"
                seats.append(Seat.from_dict(seat_data))
                self._save_unsafe(seats)
                return "Added successfully"
        except Exception as e: return f"Error: {e}"

    def update_seat(self, seat_id, seat_data, current_user=None):
        try:
            with FileLock(self.lock_path, timeout=5):
                seats = self._load_unsafe()
                target = next((s for s in seats if str(s.seat_id) == str(seat_id)), None)
                if not target: return "Seat not found"
                
                if "status" in seat_data: target.status = seat_data["status"]
                if "seat_type" in seat_data: target.seat_type = seat_data["seat_type"]
                
                self._save_unsafe(seats)
                return "Updated successfully"
        except Exception as e: return f"Error: {e}"

    def book_seat(self, sid, show_id): return self.update_seat(sid, {"status": "occupied"}, None)
    def release_seat(self, sid): return self.update_seat(sid, {"status": "available"}, None)

    # --- HÀM MỚI: TỰ ĐỘNG TẠO LAYOUT 14x11 ---
    def initialize_standard_layout(self, theater_id):
        """
        Xóa ghế cũ của rạp này và tạo lại layout chuẩn:
        - 11 Hàng (A-K), 14 Cột (1-14)
        - Hàng 0-4 (A-E): Standard
        - Hàng 5-9 (F-J): VIP
        - Hàng 10 (K): Sweetbox
        """
        try:
            with FileLock(self.lock_path, timeout=10):
                all_seats = self._load_unsafe()
                # Xóa ghế cũ của rạp này
                all_seats = [s for s in all_seats if str(s.theater_id) != str(theater_id)]
                
                new_seats = []
                rows = 11 # A -> K
                cols = 14 # 1 -> 14
                
                for r in range(rows):
                    row_char = chr(65 + r) # A, B, C...
                    
                    # Xác định loại ghế
                    s_type = "Standard"
                    if 5 <= r <= 9: s_type = "VIP"
                    elif r == 10: s_type = "Sweetbox"
                    
                    for c in range(cols):
                        seat_num = f"{row_char}{c+1}"
                        new_seats.append(Seat(None, theater_id, seat_num, "available", s_type))
                
                all_seats.extend(new_seats)
                self._save_unsafe(all_seats)
        except Exception as e:
            print(f"Lỗi khởi tạo ghế: {e}")