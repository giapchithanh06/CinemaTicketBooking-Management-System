import tkinter as tk
from tkinter import messagebox
import os
import sys
import ctypes
from PIL import Image, ImageTk

# --- Xử lý đường dẫn import ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- Import Controllers & Models ---
try:
    from controllers.auth_manager import AuthManager
    from controllers.movie_manager import MovieManager
    from controllers.ticket_manager import TicketManager
    from controllers.news_manager import NewsManager
    from controllers.notification_manager import NotificationManager
    from controllers.seat_manager import SeatManager
    from controllers.showtime_manager import ShowtimeManager
    from controllers.theater_manager import TheaterManager
    from controllers.qr_generator import generate_ticket_qr
    from services.place_ticket import PlaceTicket
    from models.user import Admin
except ImportError as e:
    messagebox.showerror("Lỗi hệ thống", f"Thiếu module: {e}")
    sys.exit(1)

# --- FIX DPI ---
try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
except: pass

class UserUI:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.root.title("Duo Cinema - Hệ thống đặt vé")
        self.root.configure(bg="#FFF5E1")
        self.current_tab = "now_showing"
        # Maximize window
        try: self.root.state('zoomed')
        except: self.root.attributes('-fullscreen', True)
        
        self.root.update_idletasks()
        self.width = self.root.winfo_width()
        self.height = self.root.winfo_height()

        if isinstance(self.user, dict) and self.user.get("type") == "Admin":
             messagebox.showinfo("Info", "Tài khoản Admin vui lòng đăng nhập ở Dashboard quản trị.")
             self.root.destroy(); return

        try:
            self.auth_manager = AuthManager()
            self.movie_manager = MovieManager(api_key="4745010e7edb2bcabed69a949bbf641b")
            self.ticket_manager = TicketManager()
            self.news_manager = NewsManager()
            self.notification_manager = NotificationManager()
            self.seat_manager = SeatManager()
            self.showtime_manager = ShowtimeManager()
            self.theater_manager = TheaterManager()
            self.now_showing = self.movie_manager.get_now_showing()
            self.upcoming = self.movie_manager.get_upcoming()
        except: self.now_showing, self.upcoming = [], []

        self.main_container = tk.Frame(self.root, bg="#FFF5E1")
        self.main_container.pack(fill="both", expand=True)

        self.place_ticket = PlaceTicket(self.main_container, self.user, self.movie_manager, self)
        
        self.load_resources()
        self.register_observers()
        
        self.create_header()
        self.create_banner()
        self.create_now_playing_section()

    def load_resources(self):
        self.img_dir = os.path.join(project_root, "images")
        def safe_load(n, s):
            p = os.path.join(self.img_dir, n)
            if os.path.exists(p): return ImageTk.PhotoImage(Image.open(p).resize(s, Image.Resampling.LANCZOS))
            return None
        self.logo_img = safe_load("logo.png", (150, 60))
        self.user_icon = safe_load("user.png", (40, 40))

    def register_observers(self):
        def on_notify(msg):
            if "phim" in msg.lower() or "movie" in msg.lower():
                self.root.after(100, self.reload_movies)
            if hasattr(self, 'current_tab') and self.current_tab == "Thông báo":
                self.create_notification_section()
        self.news_manager.register_observer(on_notify)
        self.movie_manager.register_observer(on_notify)

    def reload_movies(self):
        self.movie_manager.load_local_data()
        self.now_showing = self.movie_manager.get_now_showing()
        self.upcoming = self.movie_manager.get_upcoming()
        if self.current_tab == "Đang Chiếu": self.create_now_playing_section()
        elif self.current_tab == "Sắp Chiếu": self.create_upcoming_section()

    def create_header(self):
        header = tk.Frame(self.main_container, bg="#FFB085", height=70)
        header.pack(fill="x"); header.pack_propagate(False)
        if self.logo_img: tk.Label(header, image=self.logo_img, bg="#FFB085").pack(side="left", padx=20)
        else: tk.Label(header, text="Duo Cinema", font=("Arial", 14, "bold"), bg="#FFB085").pack(side="left", padx=20)

        nav = tk.Frame(header, bg="#FFB085"); nav.pack(side="left", expand=True)
        for t in ["Đặt vé nhanh", "Đang Chiếu", "Sắp Chiếu", "Tin tức", "Thông báo"]:
            tk.Button(nav, text=t, font=("Arial", 11, "bold"), bg="#FFB085", bd=0,
                      activebackground="#FF8C42", cursor="hand2",
                      command=lambda x=t: self.switch_tab(x)).pack(side="left", padx=15)

        right = tk.Frame(header, bg="#FFB085"); right.pack(side="right", padx=20)
        tk.Label(right, text=f"Hi, {self.user.get('full_name', 'User')}", bg="#FFB085", font=("Arial", 10, "italic")).pack(side="left", padx=5)
        if self.user_icon: tk.Button(right, image=self.user_icon, bg="#FFB085", bd=0, command=self.show_user_menu).pack(side="left")
        else: tk.Button(right, text="👤", bg="#FFB085", bd=0, command=self.show_user_menu).pack(side="left")

    def show_user_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Vé của tôi", command=self.show_my_tickets)
        menu.add_command(label="Đăng xuất", command=self.logout)
        try: menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
        except: pass

    def switch_tab(self, tab):
        self.current_tab = tab
        for w in self.main_container.winfo_children(): w.destroy()
        self.create_header()
        if tab == "Đặt vé nhanh": self.place_ticket.create_quick_booking_section()
        elif tab == "Đang Chiếu": self.create_banner(); self.create_now_playing_section()
        elif tab == "Sắp Chiếu": self.create_banner(); self.create_upcoming_section()
        elif tab == "Tin tức": self.create_news_section()
        elif tab == "Thông báo": self.create_notification_section()

    def create_banner(self):
        fr = tk.Frame(self.main_container, bg="#FFF5E1"); fr.pack(fill="x", pady=5)
        tk.Label(fr, text="🎬 Phim Hay Đang Chiếu - Đặt Vé Ngay! 🍿", font=("Arial", 18, "bold"), bg="#FFF5E1", fg="#E74C3C").pack()

    def create_now_playing_section(self):
        self.display_section("Phim Đang Chiếu", self.now_showing, allow_booking=True)

    def create_upcoming_section(self):
        self.display_section("Phim Sắp Chiếu", self.upcoming, allow_booking=False)

    def display_section(self, title, movies, allow_booking=True):
        fr = tk.Frame(self.main_container, bg="#FFF5E1"); fr.pack(fill="both", expand=True, padx=20)
        tk.Label(fr, text=title, font=("Arial", 16, "bold"), bg="#FFF5E1", fg="#003366").pack(anchor="w", pady=10)
        self.display_movies(fr, movies, allow_booking)

    def display_movies(self, parent_frame, movies, allow_booking=True):
        if not movies:
            tk.Label(parent_frame, text="Đang cập nhật phim...", bg="#FFF5E1", font=("Arial", 12)).pack(pady=20)
            return

        canvas = tk.Canvas(parent_frame, bg="#FFF5E1", highlightthickness=0)
        scrollbar = tk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        inner_frame = tk.Frame(canvas, bg="#FFF5E1")
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_scroll)
        
        # --- FIX LỖI CRASH Ở ĐÂY ---
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass # Bỏ qua lỗi nếu widget đã bị hủy
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        cols = max(4, self.width // 280)
        self.poster_imgs = [] 

        for i, m in enumerate(movies):
            row = i // cols
            col = i % cols
            
            card = tk.Frame(inner_frame, bg="white", bd=2, relief="groove")
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
            if m.poster_path and os.path.exists(m.poster_path):
                try:
                    img = Image.open(m.poster_path).resize((180, 250), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.poster_imgs.append(photo)
                    lbl = tk.Label(card, image=photo, bg="white", cursor="hand2" if allow_booking else "arrow")
                    lbl.pack(pady=5)
                    if allow_booking:
                        lbl.bind("<Button-1>", lambda e, mv=m: self.book_ticket(mv))
                except:
                    tk.Label(card, text="[Ảnh lỗi]", height=13).pack(pady=5)
            else:
                tk.Label(card, text="[Không ảnh]", height=13).pack(pady=5)
            
            tk.Label(card, text=m.title, font=("Arial", 11, "bold"), 
                     wraplength=170, bg="white", fg="#333", height=2, anchor="n").pack(pady=(0, 2))
            
            tk.Label(card, text=f"Thời lượng: {m.duration}p", font=("Arial", 9), fg="#666", bg="white").pack()
            
            if allow_booking:
                btn_fr = tk.Frame(card, bg="white")
                btn_fr.pack(side=tk.BOTTOM, fill='x', padx=15, pady=10)
                btn = tk.Button(btn_fr, text="Đặt vé", bg="#E74C3C", fg="white", font=("Arial", 10, "bold"),
                                command=lambda mv=m: self.book_ticket(mv), cursor="hand2")
                btn.pack(fill="x")
            else:
                tk.Label(card, text="Sắp khởi chiếu", bg="white", fg="#FF8C42", font=("Arial", 10, "italic")).pack(pady=10)

        for c in range(cols): inner_frame.grid_columnconfigure(c, weight=1)

    def book_ticket(self, movie):
        self.switch_tab("Đặt vé nhanh")
        if hasattr(self.place_ticket, 'movie_var'):
            self.place_ticket.movie_var.set(movie.title)
            self.place_ticket.update_showtimes()
            self.place_ticket.update_movie_info(movie.title)

    def create_news_section(self):
        fr = tk.Frame(self.main_container, bg="#FFF5E1"); fr.pack(fill="both", expand=True, padx=20)
        tk.Label(fr, text="Tin Tức & Sự Kiện", font=("Arial", 16, "bold"), bg="#FFF5E1").pack(anchor="w", pady=10)
        for news in self.news_manager.get_all_news():
            n_fr = tk.Frame(fr, bg="white", bd=1, relief="solid"); n_fr.pack(fill="x", pady=5)
            tk.Label(n_fr, text=news['title'], font=("Arial", 12, "bold"), bg="white", fg="#E74C3C").pack(anchor="w", padx=10, pady=5)
            tk.Label(n_fr, text=news['content'], bg="white").pack(anchor="w", padx=10)

    def create_notification_section(self):
        fr = tk.Frame(self.main_container, bg="#FFF5E1"); fr.pack(fill="both", expand=True, padx=20)
        tk.Label(fr, text="Thông báo của bạn", font=("Arial", 16, "bold"), bg="#FFF5E1").pack(anchor="w", pady=10)
        notis = self.notification_manager.get_notifications(self.user.get('username'))
        if not notis: tk.Label(fr, text="Không có thông báo mới.", bg="#FFF5E1", font=("Arial", 12)).pack(pady=20); return
        for n in notis:
            c = "#EEE" if n.get('read') else "#FFF"
            n_fr = tk.Frame(fr, bg=c, bd=1, relief="solid"); n_fr.pack(fill="x", pady=2)
            tk.Label(n_fr, text=n['message'], bg=c, font=("Arial", 11)).pack(side="left", padx=10, pady=10)
            if not n.get('read'): tk.Button(n_fr, text="Đã đọc", command=lambda nid=n['id']: self.read_noti(nid)).pack(side="right", padx=10)

    def read_noti(self, nid):
        self.notification_manager.delete_notification(nid); self.create_notification_section()

    def show_my_tickets(self):
        win = tk.Toplevel(self.root); win.title("Vé của tôi"); win.geometry("600x500")
        tickets = self.ticket_manager.get_tickets_by_username(self.user.get('username'))
        if not tickets: tk.Label(win, text="Bạn chưa mua vé nào.", font=("Arial", 12)).pack(pady=50); return
        canvas = tk.Canvas(win); scroll = tk.Scrollbar(win, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set); scroll.pack(side="right", fill="y"); canvas.pack(fill="both", expand=True)
        frame = tk.Frame(canvas); canvas.create_window((0,0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        for t in tickets:
            f = tk.Frame(frame, bd=1, relief="groove", bg="white"); f.pack(fill="x", padx=10, pady=5)
            tk.Label(f, text=f"PHIM: {t.movie_title}\nNgày: {t.date} | Giờ: {t.show_time}\nGhế: {', '.join(t.seats)}", justify="left").pack(side="left", padx=10, pady=10)
            tk.Button(f, text="QR Code", bg="#003366", fg="white", command=lambda tk=t: self.show_qr(tk)).pack(side="right", padx=10)

    def show_qr(self, ticket):
        path = generate_ticket_qr(ticket.to_dict())
        qr_win = tk.Toplevel(self.root); qr_win.title("Mã QR Vé")
        try:
            img = Image.open(path).resize((250, 250)); photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(qr_win, image=photo); lbl.image = photo; lbl.pack(padx=20, pady=20)
            tk.Label(qr_win, text=ticket.ticket_id, font=("Arial", 12, "bold")).pack(pady=5)
        except: tk.Label(qr_win, text="Lỗi ảnh QR").pack()

    def logout(self):
        self.auth_manager.logout(self.user.get('username'))
        self.root.destroy()
        try: from ui.login_ui import Login; new_root = tk.Tk(); Login(new_root); new_root.mainloop()
        except: pass