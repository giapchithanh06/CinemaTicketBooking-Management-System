import tkinter as tk
import uuid
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from models.ticket import Ticket
from controllers.ticket_manager import TicketManager
from controllers.movie_manager import MovieManager
from controllers.showtime_manager import ShowtimeManager
from controllers.theater_manager import TheaterManager
from controllers.seat_manager import SeatManager
from controllers.news_manager import NewsManager
from controllers.notification_manager import NotificationManager
from controllers.qr_generator import generate_ticket_qr

class PlaceTicket:
    def __init__(self, parent, user, movie_manager, user_ui):
        self.parent = parent
        self.user = user
        self.movie_manager = movie_manager
        
        self.ticket_manager = TicketManager()
        self.showtime_manager = ShowtimeManager()
        self.theater_manager = TheaterManager()
        self.seat_manager = SeatManager()
        self.news_manager = NewsManager()
        self.notification_manager = NotificationManager()
        
        self.now_showing = self.movie_manager.get_now_showing()
        self.user_ui = user_ui
        self.step = tk.IntVar(value=1)
        self.step_labels = []
        self.selected_seats = []
        self.total_price = 0
        self.popup_buttons = {} 

    def create_quick_booking_section(self):
        for w in self.parent.winfo_children(): w.destroy()
        if hasattr(self.user_ui, 'create_header'): self.user_ui.create_header()
        
        self.main_frame = tk.Frame(self.parent, bg="#FFF5E1")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Background mờ
        bg_path = os.path.join(project_root, "images", "background.jpg")
        if os.path.exists(bg_path):
            try:
                bg_img = Image.open(bg_path).resize((self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()), Image.Resampling.LANCZOS)
                overlay = Image.new('RGBA', bg_img.size, (255, 245, 225, 200))
                self.bg_photo = ImageTk.PhotoImage(Image.blend(bg_img.convert('RGBA'), overlay, 0.8))
                tk.Label(self.main_frame, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)
            except: self.main_frame.config(bg="#FFF5E1")
        else: self.main_frame.config(bg="#FFF5E1")

        # Grid chính chia 2 cột: Trái (Thao tác) - Phải (Thông tin phim)
        main_grid = tk.Frame(self.main_frame, bg="#FFF5E1")
        main_grid.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.step_frame = tk.Frame(main_grid, bg="#FFF5E1", bd=2, relief="solid")
        self.step_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.movie_info_frame = tk.Frame(main_grid, bg="#FFF5E1", bd=2, relief="solid")
        self.movie_info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        main_grid.grid_columnconfigure(0, weight=2)
        main_grid.grid_columnconfigure(1, weight=1)
        main_grid.grid_rowconfigure(0, weight=1)

        # Thanh tiến trình
        progress_frame = tk.Frame(self.step_frame, bg="#FFF5E1", bd=1, relief="raised")
        progress_frame.pack(fill="x", pady=10)
        self.step_labels = []
        for i, t in enumerate(["Chọn Phim & Suất", "Chọn Ghế", "Thanh Toán", "Vé Của Bạn"], 1):
            lbl = tk.Label(progress_frame, text=f"{i}. {t}", font=("Arial", 11, "bold"),
                           fg="#FF8C42" if self.step.get() == i else "#6D597A", bg="#FFF5E1", padx=10)
            lbl.pack(side="left"); self.step_labels.append(lbl)
            if i < 4: tk.Label(progress_frame, text=">", fg="#999", bg="#FFF5E1").pack(side="left")

        # Các Step Frame
        self.step_frames = [tk.Frame(self.step_frame, bg="#FFF5E1") for _ in range(4)]
        for f in self.step_frames: f.pack(fill="both", expand=True)

        self.setup_step_1(); self.setup_step_2(); self.setup_step_3(); self.setup_step_4()
        self.setup_movie_info(); self.show_step()

    def generate_showtimes(self, movie, selected_date):
        if not movie: return []
        all_shows = self.showtime_manager.get_all_showtimes()
        valid_shows = []
        theaters = {t["theater_id"]: t for t in self.theater_manager.get_all_theaters()}
        now = datetime.now()
        for s in all_shows:
            if s["movie_title"] == movie.title and s["date"] == selected_date:
                try:
                    st_dt = datetime.strptime(f"{s['date']} {s['show_time']}", "%d-%m-%Y %H:%M")
                    if st_dt <= now: continue
                except: pass
                t_info = theaters.get(s["theater_id"])
                t_name = t_info['name'] if t_info else s['theater_id']
                valid_shows.append(f"{s['show_time']} | {t_name}")
        return sorted(valid_shows)

    def setup_step_1(self):
        fr = self.step_frames[0]
        
        # --- Phần chọn (đẩy lên trên) ---
        tk.Label(fr, text="1. Chọn Phim:", bg="#FFF5E1", font=("Arial", 12, "bold")).pack(anchor="w", padx=50, pady=(20, 5))
        movies = [m.title for m in self.now_showing] if self.now_showing else ["Không có phim"]
        self.movie_var = tk.StringVar(value=movies[0] if movies else "")
        tk.OptionMenu(fr, self.movie_var, *movies, command=lambda v: [self.update_movie_info(v), self.update_showtimes()]).pack(anchor="w", padx=50)

        tk.Label(fr, text="2. Ngày Chiếu:", bg="#FFF5E1", font=("Arial", 12, "bold")).pack(anchor="w", padx=50, pady=(15, 5))
        today = datetime.now()
        date_list = [(today + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(8)]
        self.date_combo = ttk.Combobox(fr, values=date_list, state="readonly", font=("Arial", 11), width=30)
        self.date_combo.current(0)
        self.date_combo.pack(anchor="w", padx=50)
        self.date_combo.bind("<<ComboboxSelected>>", lambda e: self.update_showtimes())

        tk.Label(fr, text="3. Suất Chiếu:", bg="#FFF5E1", font=("Arial", 12, "bold")).pack(anchor="w", padx=50, pady=(15, 5))
        self.time_var = tk.StringVar(value="")
        self.time_menu = tk.OptionMenu(fr, self.time_var, "")
        self.time_menu.config(width=35); self.time_menu.pack(anchor="w", padx=50)

        tk.Button(fr, text="Tiếp Theo ➤", bg="#FF8C42", fg="white", font=("Arial", 12, "bold"), command=self.next_step, padx=30, pady=5).pack(pady=30)
        
        # --- [MỚI] Phần lấp đầy khoảng trống bên dưới ---
        note_frame = tk.Frame(fr, bg="#FFF8DC", bd=1, relief="solid", padx=10, pady=10)
        note_frame.pack(fill="x", padx=50, pady=10, side="bottom")
        
        tk.Label(note_frame, text="LƯU Ý QUAN TRỌNG:", font=("Arial", 11, "bold"), bg="#FFF8DC", fg="#E74C3C").pack(anchor="w")
        notes = [
            "• Vui lòng đến trước giờ chiếu 15 phút.",
            "• Vé đã mua không thể hoàn tiền.",
            "• Trẻ em dưới 13 tuổi cần người lớn đi kèm.",
            "• Không mang thức ăn bên ngoài vào rạp."
        ]
        for n in notes:
            tk.Label(note_frame, text=n, font=("Arial", 10), bg="#FFF8DC", fg="#333").pack(anchor="w")

        self.update_showtimes()

    def update_showtimes(self, *args):
        title = self.movie_var.get()
        date_str = self.date_combo.get()
        movie = next((m for m in self.now_showing if m.title == title), None)
        shows = self.generate_showtimes(movie, date_str)
        menu = self.time_menu["menu"]; menu.delete(0, "end")
        if shows:
            self.time_var.set(shows[0])
            for s in shows: menu.add_command(label=s, command=lambda v=s: self.time_var.set(v))
        else: self.time_var.set("Không có suất chiếu")

    def setup_step_2(self):
        fr = self.step_frames[1]
        self.seat_info_lbl = tk.Label(fr, text="", bg="#FFF5E1", font=("Arial", 11, "bold"), fg="#333")
        self.seat_info_lbl.pack(pady=(10, 5))
        
        legend_frame = tk.Frame(fr, bg="#FFF5E1"); legend_frame.pack(pady=5)
        colors = [("Thường", "#2ECC71"), ("VIP", "#F39C12"), ("Sweetbox", "#E91E63"), ("Đã đặt", "#E74C3C"), ("Đang chọn", "#3498DB")]
        for txt, clr in colors: tk.Label(legend_frame, text=f" {txt} ", bg=clr, fg="white", font=("Arial", 8, "bold")).pack(side="left", padx=5)

        self.map_container = tk.Frame(fr, bg="white", bd=2, relief="sunken")
        self.map_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.selection_lbl = tk.Label(fr, text="Chưa chọn ghế", bg="#FFF5E1", font=("Arial", 12, "bold"), fg="#E74C3C")
        self.selection_lbl.pack(pady=10)

        nav = tk.Frame(fr, bg="#FFF5E1"); nav.pack(side="bottom", pady=20)
        tk.Button(nav, text="❮ Quay Lại", command=self.prev_step).pack(side="left", padx=10)
        tk.Button(nav, text="Tiếp Theo ➤", bg="#FF8C42", fg="white", font=("Arial", 11, "bold"), command=self.next_step).pack(side="left", padx=10)

    def render_inline_seat_map(self, theater_id):
        for widget in self.map_container.winfo_children(): widget.destroy()
        
        try: self.seat_manager = SeatManager()
        except: pass

        tk.Label(self.map_container, text=f"MÀN HÌNH (RẠP {theater_id})", bg="black", fg="white", font=("Arial", 10, "bold")).pack(fill="x", pady=(0, 10))
        seat_frame = tk.Frame(self.map_container, bg="white"); seat_frame.pack(expand=True)

        seats = self.seat_manager.get_seats_by_theater(theater_id)
        if not seats:
            self.seat_manager.initialize_standard_layout(theater_id)
            seats = self.seat_manager.get_seats_by_theater(theater_id)

        try:
            time_val = self.time_var.get()
            if " | " in time_val:
                time_str, room_name = time_val.split(" | ")
                booked_seats = self.ticket_manager.get_occupied_seats(self.movie_var.get(), self.date_combo.get(), time_str, room_name)
            else: booked_seats = []
        except: booked_seats = []

        rows, cols = 11, 14
        self.popup_buttons = {} 

        for r in range(rows):
            for c in range(cols):
                seat_num = f"{chr(65+r)}{c+1}"
                s_obj = next((s for s in seats if s["seat_number"] == seat_num), None)
                
                row_type = "Standard"; bg_color = "#2ECC71" 
                if 5 <= r <= 9: row_type = "VIP"; bg_color = "#F39C12"
                elif r == 10: row_type = "Sweetbox"; bg_color = "#E91E63"
                
                state = "normal"
                
                if s_obj:
                    if s_obj["status"] == "broken": bg_color = "#95A5A6"; state = "disabled"
                    elif s_obj["status"] == "available" and s_obj.get("seat_type"):
                         if s_obj["seat_type"] == "VIP" and state != "disabled": bg_color = "#F39C12"
                         elif s_obj["seat_type"] == "Sweetbox" and state != "disabled": bg_color = "#E91E63"
                
                if seat_num in booked_seats: bg_color = "#E74C3C"; state = "disabled"
                if seat_num in self.selected_seats: bg_color = "#3498DB" 

                btn = tk.Button(seat_frame, text=seat_num, bg=bg_color, fg="white", font=("Arial", 8, "bold"), relief="flat", state=state, width=4)
                btn.grid(row=r, column=c, padx=1, pady=1)
                self.popup_buttons[seat_num] = btn
                btn.config(command=lambda sn=seat_num, b=btn, rt=row_type: self.on_popup_seat_click(sn, b, rt))

    def on_popup_seat_click(self, seat_num, btn, row_type):
        target_seats = [seat_num]
        if row_type == "Sweetbox":
            row_char = seat_num[0]
            try:
                col_num = int(seat_num[1:])
                neighbor_col = col_num + 1 if col_num % 2 != 0 else col_num - 1
                neighbor_id = f"{row_char}{neighbor_col}"
                if neighbor_id in self.popup_buttons:
                    neighbor_btn = self.popup_buttons[neighbor_id]
                    if neighbor_btn['state'] == 'disabled':
                        messagebox.showwarning("Thông báo", "Ghế đôi này không khả dụng."); return 
                    target_seats.append(neighbor_id)
            except: pass

        is_selecting = seat_num not in self.selected_seats
        for s_id in target_seats:
            if s_id not in self.popup_buttons: continue
            s_btn = self.popup_buttons[s_id]
            if is_selecting:
                if s_id not in self.selected_seats: self.selected_seats.append(s_id); s_btn.config(bg="#3498DB")
            else:
                if s_id in self.selected_seats:
                    self.selected_seats.remove(s_id)
                    orig_bg = "#2ECC71"
                    if row_type == "VIP": orig_bg = "#F39C12"
                    elif row_type == "Sweetbox": orig_bg = "#E91E63"
                    s_btn.config(bg=orig_bg)
        self.update_price_display()

    def update_price_display(self):
        total = 0
        for sn in self.selected_seats:
            row_char = sn[0]
            if row_char == 'K': price = 120000 
            elif row_char in ['F','G','H','I','J']: price = 100000
            else: price = 80000
            total += price
        self.total_price = total
        self.selection_lbl.config(text=f"Ghế: {', '.join(self.selected_seats)}\nTổng tiền: {total:,} đ")

    def setup_step_3(self):
        fr = self.step_frames[2]
        tk.Label(fr, text="Xác Nhận Thông Tin", bg="#FFF5E1", font=("Arial", 16, "bold"), fg="#E74C3C").pack(pady=20)
        self.confirm_lbl = tk.Label(fr, text="", bg="#FFF5E1", font=("Arial", 12), justify="left"); self.confirm_lbl.pack(pady=10)
        f = tk.Frame(fr, bg="#FFF5E1"); f.pack()
        tk.Label(f, text="Họ Tên:", bg="#FFF5E1").grid(row=0, column=0, sticky="e")
        self.ne = tk.Entry(f, width=30); self.ne.grid(row=0, column=1); self.ne.insert(0, self.user.get("full_name", ""))
        tk.Label(f, text="Email:", bg="#FFF5E1").grid(row=1, column=0, sticky="e")
        self.ee = tk.Entry(f, width=30); self.ee.grid(row=1, column=1); self.ee.insert(0, self.user.get("email", ""))
        tk.Label(f, text="SĐT:", bg="#FFF5E1").grid(row=2, column=0, sticky="e")
        self.pe = tk.Entry(f, width=30); self.pe.grid(row=2, column=1); self.pe.insert(0, self.user.get("phone", ""))
        nav = tk.Frame(fr, bg="#FFF5E1"); nav.pack(side="bottom", pady=30)
        tk.Button(nav, text="❮ Quay Lại", command=self.prev_step).pack(side="left", padx=10)
        tk.Button(nav, text="THANH TOÁN ➤", bg="#E74C3C", fg="white", font=("Arial", 12, "bold"), command=self.process_payment).pack(side="left", padx=10)

    def process_payment(self):
        if not self.selected_seats: return messagebox.showerror("Lỗi", "Chưa chọn ghế!")
        try:
            time, room = self.time_var.get().split(" | ")
            data = {
                "ticket_id": str(uuid.uuid4()), "username": self.user.get("username"),
                "movie_title": self.movie_var.get(), "show_time": time,
                "date": self.date_combo.get(), "room": room, "seats": self.selected_seats,
                "price": self.total_price, "name": self.ne.get(), "email": self.ee.get(), "phone": self.pe.get(), "payment_method": "Cash"
            }
            if "Added" in self.ticket_manager.add_ticket(data, self.user):
                self.final_ticket = data
                self.next_step()
                messagebox.showinfo("Thành công", "Đặt vé thành công!")
            else: messagebox.showerror("Lỗi", "Không thể tạo vé.")
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def setup_step_4(self):
        fr = self.step_frames[3]
        tk.Label(fr, text="VÉ ĐIỆN TỬ", font=("Arial", 18, "bold"), bg="#FFF5E1", fg="#27AE60").pack(pady=20)
        self.td_lbl = tk.Label(fr, text="", bg="white", padx=20, pady=20, font=("Courier", 11), justify="left", relief="solid"); self.td_lbl.pack()
        self.qr_lbl = tk.Label(fr, bg="#FFF5E1"); self.qr_lbl.pack(pady=10)
        tk.Button(fr, text="Về Trang Chủ", bg="#003366", fg="white", command=self.finish).pack(pady=20)

    def display_final_ticket(self):
        t = self.final_ticket
        self.td_lbl.config(text=f"MÃ: {t['ticket_id']}\nPHIM: {t['movie_title']}\nNGÀY: {t['date']} {t['show_time']}\nRẠP: {t['room']} - GHẾ: {', '.join(t['seats'])}\nTỔNG: {t['price']:,} đ")
        try:
            img = Image.open(generate_ticket_qr(t)).resize((150, 150))
            self.qr_p = ImageTk.PhotoImage(img); self.qr_lbl.config(image=self.qr_p)
        except: pass

    def next_step(self):
        if self.step.get() == 1:
            val = self.time_var.get()
            if not val or " | " not in val: return messagebox.showwarning("Lỗi", "Vui lòng chọn suất chiếu hợp lệ (Giờ | Rạp)")
            self.seat_info_lbl.config(text=f"{self.movie_var.get()} | {val}")
            _, room_name = val.split(" | ")
            theaters = self.theater_manager.get_all_theaters()
            tid = next((t["theater_id"] for t in theaters if t["name"] == room_name), room_name)
            self.render_inline_seat_map(tid)
        elif self.step.get() == 2:
            if not self.selected_seats: return messagebox.showwarning("Lỗi", "Vui lòng chọn ghế")
            self.confirm_lbl.config(text=f"Phim: {self.movie_var.get()}\nSuất: {self.time_var.get()}\nGhế: {', '.join(self.selected_seats)}\nTổng: {self.total_price:,} đ")
        self.step.set(self.step.get() + 1); self.show_step()
        if self.step.get() == 4: self.display_final_ticket()

    def prev_step(self): self.step.set(self.step.get() - 1); self.show_step()
    def show_step(self):
        for f in self.step_frames: f.pack_forget()
        if 1 <= self.step.get() <= 4: self.step_frames[self.step.get()-1].pack(fill="both", expand=True)
        for i, l in enumerate(self.step_labels, 1): l.config(fg="#FF8C42" if i == self.step.get() else "#6D597A")
    def finish(self): self.selected_seats = []; self.step.set(1); self.user_ui.switch_tab("Đang Chiếu")
    
    def setup_movie_info(self):
        # --- [MỚI] Phần thông tin phim bên phải (lấp đầy hơn) ---
        self.pl = tk.Label(self.movie_info_frame, bg="#FFF5E1"); self.pl.pack(pady=20)
        self.mt = tk.Label(self.movie_info_frame, text="", font=("Arial", 16, "bold"), bg="#FFF5E1", wraplength=200, fg="#003366"); self.mt.pack()
        
        info_sub = tk.Frame(self.movie_info_frame, bg="#FFF5E1"); info_sub.pack(pady=20, padx=10)
        self.md = tk.Label(info_sub, text="", bg="#FFF5E1", wraplength=200, justify="left", font=("Arial", 10)); self.md.pack()
        
        # Thêm các nhãn giả lập thông tin (lấp đầy)
        tk.Label(info_sub, text="\n----------------", bg="#FFF5E1").pack()
        tk.Label(info_sub, text="Đạo diễn: Christopher Nolan\nDiễn viên: Cillian Murphy, Emily Blunt", 
                 bg="#FFF5E1", wraplength=200, justify="center", font=("Arial", 9, "italic")).pack(pady=10)

    def update_movie_info(self, title):
        m = next((x for x in self.now_showing if x.title == title), None)
        if m:
            self.mt.config(text=m.title)
            self.md.config(text=f"Thể loại: {m.genre}\nThời lượng: {m.duration} phút\nKhởi chiếu: {m.release_date}")
            if m.poster_path and os.path.exists(m.poster_path):
                self.pp = ImageTk.PhotoImage(Image.open(m.poster_path).resize((200, 300))); self.pl.config(image=self.pp)