import json
import os
import threading
from datetime import datetime
from filelock import FileLock
from models.ticket import Ticket
from controllers.seat_manager import SeatManager
from controllers.theater_manager import TheaterManager

class TicketManager:
    def __init__(self, json_file_path="data/tickets.json"):
        self.json_file_path = json_file_path
        self.tickets = []
        
        self.seat_manager = SeatManager()
        self.theater_manager = TheaterManager()
        
        os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
        self.load_tickets()

    def load_tickets(self):
        """Tải vé và chuyển đổi sang Object Ticket"""
        self.tickets = []
        if os.path.exists(self.json_file_path):
            try:
                if os.path.getsize(self.json_file_path) == 0: return
                with FileLock(f"{self.json_file_path}.lock", timeout=2):
                    with open(self.json_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.tickets = []
                            for t in data:
                                try:
                                    # Chuẩn hóa dữ liệu cũ
                                    if isinstance(t, dict) and "status" not in t:
                                        t["status"] = "valid"
                                    
                                    if isinstance(t, dict):
                                        self.tickets.append(Ticket.from_dict(t))
                                    else:
                                        self.tickets.append(t)
                                except: pass
            except Exception as e:
                print(f"[TicketManager] Lỗi tải file: {e}")
                self.tickets = []

    def save_tickets(self):
        """Lưu vé: Chuyển Object về Dict trước khi lưu"""
        data = []
        for t in self.tickets:
            if hasattr(t, 'to_dict'):
                data.append(t.to_dict())
            elif isinstance(t, dict):
                data.append(t)
        
        try:
            with FileLock(f"{self.json_file_path}.lock"):
                with open(self.json_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[TicketManager] Lỗi lưu file: {e}")

    def get_all_tickets(self):
        """Trả về list dict cho UI hiển thị"""
        self.load_tickets()
        result = []
        for t in self.tickets:
            t_dict = t.to_dict() if hasattr(t, 'to_dict') else t
            if "status" not in t_dict: t_dict["status"] = "valid"
            result.append(t_dict)
        return result

    def get_occupied_seats(self, movie_title, date_str, time_str, room_name):
        """
        [QUAN TRỌNG] Tìm các ghế đã bán cho một suất chiếu cụ thể.
        Logic này thay thế việc check trạng thái trong seats.json
        """
        self.load_tickets()
        occupied = []
        
        s_movie = str(movie_title).strip().lower()
        s_date = str(date_str).strip()
        s_time = str(time_str).strip()
        s_room = str(room_name).strip().lower()

        for t in self.tickets:
            td = t.to_dict() if hasattr(t, 'to_dict') else t
            
            # Bỏ qua vé đã hủy
            if td.get("status") == "cancelled": continue

            # So sánh 4 điều kiện
            if (str(td.get("movie_title")).strip().lower() == s_movie and
                str(td.get("date")).strip() == s_date and
                str(td.get("show_time")).strip() == s_time and
                str(td.get("room")).strip().lower() == s_room):
                
                seats = td.get("seats", [])
                if isinstance(seats, list): occupied.extend(seats)
                else: occupied.append(str(seats))
                
        return occupied

    def add_ticket(self, ticket_data, user):
        try:
            if hasattr(ticket_data, 'to_dict'):
                ticket_data = ticket_data.to_dict()
            
            # Luôn đặt trạng thái là valid khi tạo mới
            ticket_data["status"] = "valid"
                
            new_ticket = Ticket.from_dict(ticket_data)
            self.tickets.append(new_ticket)
            self.save_tickets()
            return "Added successfully"
        except Exception as e:
            return f"Error: {e}"

    def delete_ticket(self, ticket_id):
        """
        [XÓA MỀM] Chỉ đổi trạng thái sang 'cancelled'.
        Không hoàn trả ghế về 'available' trong seats.json vì logic mới
        không còn dựa vào seats.json để check ghế trống nữa.
        """
        self.load_tickets()
        
        found = False
        for t in self.tickets:
            tid = t.ticket_id if hasattr(t, 'ticket_id') else t.get('ticket_id')
            if str(tid) == str(ticket_id):
                if hasattr(t, 'status'): t.status = "cancelled"
                elif isinstance(t, dict): t["status"] = "cancelled"
                found = True
                break
        
        if found:
            self.save_tickets()
            return "Deleted (Cancelled)"
        return "Ticket not found"

    def get_tickets_by_username(self, username):
        self.load_tickets()
        user_tickets = []
        for t in self.tickets:
            u = t.username if hasattr(t, 'username') else t.get('username')
            if str(u) == str(username):
                if isinstance(t, dict):
                    user_tickets.append(Ticket.from_dict(t))
                else:
                    user_tickets.append(t)
        return user_tickets