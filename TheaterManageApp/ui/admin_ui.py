import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import sys
import subprocess
from PIL import Image, ImageTk
from datetime import datetime
import uuid
from collections import Counter
import re

# --- Xử lý đường dẫn import ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- Import các Controllers ---
try:
    from controllers.ticket_manager import TicketManager
    from controllers.showtime_manager import ShowtimeManager
    from controllers.theater_manager import TheaterManager
    from controllers.seat_manager import SeatManager
    from controllers.movie_manager import MovieManager
    from controllers.auth_manager import AuthManager
    from controllers.news_manager import NewsManager
    from controllers.notification_manager import NotificationManager
except ImportError as e:
    print(f"Lỗi Import Controller: {e}")

class AdminDashboard(tk.Tk):
    def __init__(self, admin_dict):
        super().__init__()
        self.title("Duo Cinema - Admin Dashboard")
        
        # Tự động phóng to màn hình
        try: self.state('zoomed') 
        except: self.attributes('-fullscreen', True)
        
        self.configure(bg="#f0f0f0")

        # --- Khởi tạo Manager ---
        try:
            self.auth_manager = AuthManager()
            self.movie_manager = MovieManager(api_key="4745010e7edb2bcabed69a949bbf641b") 
            self.ticket_manager = TicketManager()
            self.showtime_manager = ShowtimeManager()
            self.theater_manager = TheaterManager()
            self.seat_manager = SeatManager()
            self.news_manager = NewsManager(auth_manager=self.auth_manager)
            self.notification_manager = NotificationManager()
        except Exception as e:
            messagebox.showerror("Lỗi Hệ Thống", f"Không thể khởi tạo dữ liệu: {e}")
            self.destroy(); return

        # --- Xử lý thông tin Admin an toàn ---
        self.admin_info = self.safe_data_convert(admin_dict)
        if not self.admin_info:
            try:
                users = self.auth_manager.get_all_users()
                for user in users:
                    u = self.safe_data_convert(user)
                    if u.get("type") == "Admin" and u.get("is_logged_in"):
                        self.admin_info = u; break
            except: pass
        
        if not self.admin_info: 
            self.admin_info = {"username": "Unknown", "full_name": "Admin", "user_id": "0"}

        # Trạng thái Menu
        self.movie_menu_visible = False
        self.cinema_menu_visible = False
        self.news_menu_visible = False

        # Layout Chính
        self.create_sidebar()
        self.main_frame = tk.Frame(self, bg="white")
        self.main_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)
        
        self.register_observers()
        self.show_dashboard_home()

    # --- CÁC HÀM HỖ TRỢ AN TOÀN ---
    def safe_data_convert(self, item):
        try:
            if item is None: return {}
            if isinstance(item, dict): return item
            if hasattr(item, 'to_dict'): return item.to_dict()
            if hasattr(item, '__dict__'): return item.__dict__
            return {} 
        except: return {}

    def safe_int_convert(self, value):
        try:
            if isinstance(value, (int, float)): return int(value)
            s = str(value); s_clean = re.sub(r'[^\d]', '', s) 
            return int(s_clean) if s_clean else 0
        except: return 0

    def register_observers(self):
        def on_notify(msg):
            if hasattr(self, 'notification_manager') and self.notification_manager:
                self.notification_manager.receive_notification(msg)
            self.log_action("System", msg)
        managers = [self.movie_manager, self.theater_manager, self.seat_manager, 
                    self.showtime_manager, self.news_manager, self.ticket_manager]
        for mgr in managers:
            if hasattr(mgr, 'register_observer'): mgr.register_observer(on_notify)

    def log_action(self, actor, action):
        try:
            log_file = os.path.join(project_root, "data", "audit_logs.json")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            entry = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "actor": actor, "action": action}
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f: logs = json.load(f)
                except: logs = []
            logs.insert(0, entry)
            if len(logs) > 1000: logs = logs[:1000]
            with open(log_file, "w", encoding="utf-8") as f: json.dump(logs, f, indent=4, ensure_ascii=False)
        except: pass

    # --- GIAO DIỆN SIDEBAR ---
    def create_sidebar(self):
        sidebar = tk.Frame(self, bg="#001F3F", width=240)
        sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        tk.Label(sidebar, text="QUẢN TRỊ VIÊN", fg="white", bg="#001F3F", font=("Arial", 16, "bold")).pack(pady=(30, 20))
        self.create_menu_button(sidebar, "🏠 Tổng quan (Home)", self.show_dashboard_home)
        self.create_menu_button(sidebar, "👤 Thông tin cá nhân", self.show_admin_info)
        self.create_menu_button(sidebar, "💰 Thống kê doanh thu", self.show_revenue_stats)
        self.create_menu_button(sidebar, "📜 Lịch sử hoạt động", self.show_audit_logs)
        
        self.movie_btn = self.create_menu_button(sidebar, "🎬 Quản lý phim ▼", self.toggle_movie_menu)
        self.movie_submenu = tk.Frame(sidebar, bg="#001F3F")
        self.create_submenu_item(self.movie_submenu, "Danh sách phim", self.show_movie_list)
        self.create_submenu_item(self.movie_submenu, "Thêm phim mới", self.add_movie)
        
        self.cinema_btn = self.create_menu_button(sidebar, "🏢 Quản lý rạp ▼", self.toggle_cinema_menu)
        self.cinema_submenu = tk.Frame(sidebar, bg="#001F3F")
        self.create_submenu_item(self.cinema_submenu, "Thông tin rạp", self.show_cinema_info)
        self.create_submenu_item(self.cinema_submenu, "Quản lý suất chiếu", self.show_showtime_list)
        self.create_submenu_item(self.cinema_submenu, "Quản lý phòng chiếu", self.show_theater_list)
        self.create_submenu_item(self.cinema_submenu, "Quản lý ghế ngồi", self.show_seat_list)
        
        self.create_menu_button(sidebar, "🎟 Quản lý vé", self.show_ticket_list)
        self.create_menu_button(sidebar, "👥 Quản lý người dùng", self.show_user_list)
        self.news_btn = self.create_menu_button(sidebar, "📰 Quản lý tin tức ▼", self.toggle_news_menu)
        self.news_submenu = tk.Frame(sidebar, bg="#001F3F")
        self.create_submenu_item(self.news_submenu, "Danh sách tin tức", self.show_news_list)
        self.create_submenu_item(self.news_submenu, "Thêm tin tức", self.add_news)
        tk.Button(sidebar, text="Đăng xuất", bg="#C0392B", fg="white", font=("Arial", 11, "bold"), relief="flat", cursor="hand2", command=self.logout).pack(side="bottom", fill="x", pady=20, padx=10)

    def create_menu_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, bg="#003366", fg="white", font=("Arial", 11), relief="flat", anchor="w", padx=20, pady=10, cursor="hand2", command=command)
        btn.pack(fill="x", pady=1); return btn
    def create_submenu_item(self, parent, text, command):
        btn = tk.Button(parent, text=f"  • {text}", bg="#001F3F", fg="#CCCCCC", font=("Arial", 10), relief="flat", anchor="w", padx=40, pady=5, cursor="hand2", command=command)
        btn.pack(fill="x")
    def toggle_movie_menu(self):
        if self.movie_menu_visible: self.movie_submenu.pack_forget(); self.movie_btn.config(text="🎬 Quản lý phim ▼")
        else: self.movie_submenu.pack(after=self.movie_btn, fill="x"); self.movie_btn.config(text="🎬 Quản lý phim ▲")
        self.movie_menu_visible = not self.movie_menu_visible
    def toggle_cinema_menu(self):
        if self.cinema_menu_visible: self.cinema_submenu.pack_forget(); self.cinema_btn.config(text="🏢 Quản lý rạp ▼")
        else: self.cinema_submenu.pack(after=self.cinema_btn, fill="x"); self.cinema_btn.config(text="🏢 Quản lý rạp ▲")
        self.cinema_menu_visible = not self.cinema_menu_visible
    def toggle_news_menu(self):
        if self.news_menu_visible: self.news_submenu.pack_forget(); self.news_btn.config(text="📰 Quản lý tin tức ▼")
        else: self.news_submenu.pack(after=self.news_btn, fill="x"); self.news_btn.config(text="📰 Quản lý tin tức ▲")
        self.news_menu_visible = not self.news_menu_visible
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()

    def logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            self.log_action(self.admin_info.get("username", "Unknown"), "Đăng xuất hệ thống")
            try: self.auth_manager.logout(self.admin_info.get("username"))
            except: pass
            self.destroy()
            target_file = sys.argv[0]
            if not os.path.exists(target_file): target_file = "TheaterManageApp.py"
            try: subprocess.Popen([sys.executable, target_file])
            except: pass

    # =========================================================================
    # DASHBOARD
    # =========================================================================
    def show_dashboard_home(self):
        self.clear_main_frame()
        header = tk.Frame(self.main_frame, bg="white"); header.pack(fill="x", pady=20, padx=20)
        tk.Label(header, text=f"Xin chào, {self.admin_info.get('full_name')}! 👋", font=("Arial", 24, "bold"), bg="white", fg="#003366").pack(anchor="w")
        tk.Label(header, text=f"Hôm nay là: {datetime.now().strftime('%d/%m/%Y')}", font=("Arial", 12), bg="white", fg="#666").pack(anchor="w")
        
        today_str = datetime.now().strftime("%d-%m-%Y")
        rev_today = 0; tickets_today_count = 0; customers_today_set = set()
        recent_transactions = []; movie_revenues = Counter()

        try:
            tickets = self.ticket_manager.get_all_tickets()
            for t in reversed(tickets):
                t = self.safe_data_convert(t)
                if t.get('status') != 'valid': continue
                
                price = self.safe_int_convert(t.get('price', 0))
                title = t.get('movie_title', 'Unknown')
                movie_revenues[title] += price
                if len(recent_transactions) < 8:
                    recent_transactions.append((t.get('ticket_id')[:8], title, f"{price:,}", t.get('date')))
                
                if t.get('date') == today_str:
                    rev_today += price
                    tickets_today_count += 1
                    if t.get('username'): customers_today_set.add(t.get('username'))
        except: pass

        try:
            movies_data = self.movie_manager.get_all_movies()
            if isinstance(movies_data, dict): now_showing_count = len(movies_data.get("now_showing", []))
            else: now_showing_count = 0
        except: now_showing_count = 0
            
        cards = tk.Frame(self.main_frame, bg="white"); cards.pack(fill="x", padx=20, pady=10)
        for i in range(4): cards.columnconfigure(i, weight=1)
        
        def create_card(parent, title, value, icon_char, bg_color, col_idx):
            card = tk.Frame(parent, bg=bg_color, bd=1, relief="raised")
            card.grid(row=0, column=col_idx, padx=10, sticky="nsew", ipady=20)
            tk.Label(card, text=icon_char, font=("Arial", 30), bg=bg_color, fg="white").pack(pady=(10, 5))
            tk.Label(card, text=title, font=("Arial", 12, "bold"), bg=bg_color, fg="white").pack()
            tk.Label(card, text=value, font=("Arial", 20, "bold"), bg=bg_color, fg="white").pack(pady=5)

        create_card(cards, "DOANH THU HÔM NAY", f"{rev_today:,} đ", "💰", "#27AE60", 0)
        create_card(cards, "VÉ BÁN HÔM NAY", f"{tickets_today_count} vé", "🎟", "#E67E22", 1)
        create_card(cards, "PHIM ĐANG CHIẾU", f"{now_showing_count} phim", "🎬", "#2980B9", 2)
        create_card(cards, "KHÁCH MUA HÔM NAY", f"{len(customers_today_set)} người", "👥", "#8E44AD", 3)

        action_frame = tk.Frame(self.main_frame, bg="white"); action_frame.pack(fill="x", padx=20, pady=(20, 10))
        tk.Label(action_frame, text="Truy cập nhanh:", font=("Arial", 14, "bold"), bg="white", fg="#333").pack(anchor="w")
        btn_grid = tk.Frame(action_frame, bg="white"); btn_grid.pack(anchor="w", pady=5)
        tk.Button(btn_grid, text="Thêm Phim Mới", bg="#003366", fg="white", width=20, height=2, command=self.add_movie).grid(row=0, column=0, padx=(0,10))
        tk.Button(btn_grid, text="Quản Lý Suất Chiếu", bg="#003366", fg="white", width=20, height=2, command=self.show_showtime_list).grid(row=0, column=1, padx=10)
        tk.Button(btn_grid, text="Kiểm Tra Vé", bg="#003366", fg="white", width=20, height=2, command=self.show_ticket_list).grid(row=0, column=2, padx=10)

        detail_frame = tk.Frame(self.main_frame, bg="white"); detail_frame.pack(fill="both", expand=True, padx=20, pady=20)
        left_col = tk.Frame(detail_frame, bg="white", bd=1, relief="solid"); left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(left_col, text="🏆 Top Phim Doanh Thu Cao", font=("Arial", 12, "bold"), bg="#F1C40F", fg="#333", pady=8).pack(fill="x")
        cols_top = ("movie", "rev"); tree_top = ttk.Treeview(left_col, columns=cols_top, show="headings", height=8)
        tree_top.heading("movie", text="Tên Phim"); tree_top.column("movie", width=200)
        tree_top.heading("rev", text="Tổng Thu"); tree_top.column("rev", width=100, anchor="e")
        tree_top.pack(fill="both", expand=True, padx=5, pady=5)
        for m, r in movie_revenues.most_common(10): tree_top.insert("", "end", values=(m, f"{r:,}"))

        right_col = tk.Frame(detail_frame, bg="white", bd=1, relief="solid"); right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        tk.Label(right_col, text="🕒 Giao Dịch Vừa Qua", font=("Arial", 12, "bold"), bg="#3498DB", fg="white", pady=8).pack(fill="x")
        cols_trans = ("id", "movie", "price", "date"); tree_trans = ttk.Treeview(right_col, columns=cols_trans, show="headings", height=8)
        tree_trans.heading("id", text="Mã Vé"); tree_trans.column("id", width=80)
        tree_trans.heading("movie", text="Phim"); tree_trans.column("movie", width=150)
        tree_trans.heading("price", text="Giá"); tree_trans.column("price", width=80, anchor="e")
        tree_trans.heading("date", text="Ngày"); tree_trans.column("date", width=80, anchor="center")
        tree_trans.pack(fill="both", expand=True, padx=5, pady=5)
        for item in recent_transactions: tree_trans.insert("", "end", values=item)

    # =========================================================================
    # THỐNG KÊ DOANH THU
    # =========================================================================
    def show_revenue_stats(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Thống Kê Doanh Thu Theo Tháng", font=("Arial", 22, "bold"), bg="white", fg="#003366").pack(pady=15)

        toolbar = tk.Frame(self.main_frame, bg="white"); toolbar.pack(fill="x", padx=20, pady=5)
        tk.Label(toolbar, text="Chọn Tháng:", bg="white", font=("Arial", 11)).pack(side="left", padx=5)
        month_var = tk.StringVar(value=str(datetime.now().month))
        cb_month = ttk.Combobox(toolbar, textvariable=month_var, values=[str(i) for i in range(1, 13)], width=5, state="readonly")
        cb_month.pack(side="left", padx=5)
        tk.Label(toolbar, text="Năm:", bg="white", font=("Arial", 11)).pack(side="left", padx=5)
        year_var = tk.StringVar(value=str(datetime.now().year))
        entry_year = tk.Entry(toolbar, textvariable=year_var, width=10); entry_year.pack(side="left", padx=5)

        summary_frame = tk.Frame(self.main_frame, bg="#FFF5E1", bd=1, relief="solid"); summary_frame.pack(fill="x", padx=20, pady=10)
        lbl_total = tk.Label(summary_frame, text="TỔNG DOANH THU: 0 VNĐ", font=("Arial", 16, "bold"), bg="#FFF5E1", fg="#E74C3C", pady=20)
        lbl_total.pack()

        split_frame = tk.Frame(self.main_frame, bg="white"); split_frame.pack(fill="both", expand=True, padx=20)
        left_frame = tk.Frame(split_frame, bg="white"); left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(left_frame, text="Chi tiết từng ngày", font=("Arial", 12, "bold"), bg="white").pack(pady=5)
        tree = ttk.Treeview(left_frame, columns=("date", "count", "revenue"), show="headings", height=10)
        tree.heading("date", text="Ngày"); tree.heading("count", text="Số Vé"); tree.heading("revenue", text="Doanh Thu")
        tree.pack(fill="both", expand=True)

        right_frame = tk.Frame(split_frame, bg="white"); right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        tk.Label(right_frame, text="Top Phim Trong Tháng", font=("Arial", 12, "bold"), bg="white").pack(pady=5)
        tree2 = ttk.Treeview(right_frame, columns=("movie", "total"), show="headings", height=10)
        tree2.heading("movie", text="Tên Phim"); tree2.heading("total", text="Tổng Thu")
        tree2.pack(fill="both", expand=True)

        def filter_revenue():
            s_month = month_var.get().zfill(2); s_year = year_var.get()
            for i in tree.get_children(): tree.delete(i)
            for i in tree2.get_children(): tree2.delete(i)
            tickets = self.ticket_manager.get_all_tickets()
            stats = {}; movie_sales = Counter(); total = 0
            for t in tickets:
                t = self.safe_data_convert(t)
                if t.get('status') != 'valid': continue
                date_str = t.get('date')
                if not date_str: continue
                try:
                    d, m, y = date_str.split('-')
                    if m == s_month and y == s_year:
                        price = self.safe_int_convert(t.get('price', 0))
                        if d not in stats: stats[d] = {'count': 0, 'rev': 0}
                        stats[d]['count'] += 1; stats[d]['rev'] += price
                        movie_sales[t.get('movie_title', 'Unknown')] += price
                        total += price
                except: continue
            lbl_total.config(text=f"TỔNG DOANH THU THÁNG {s_month}/{s_year}: {total:,} VNĐ")
            for d in sorted(stats.keys(), key=int):
                tree.insert("", "end", values=(f"{d}-{s_month}-{s_year}", stats[d]['count'], f"{stats[d]['rev']:,}"))
            for m, tot in movie_sales.most_common(5):
                tree2.insert("", "end", values=(m, f"{tot:,}"))

        tk.Button(toolbar, text="Xem Thống Kê", bg="#333", fg="white", command=filter_revenue).pack(side="left", padx=10)
        filter_revenue()

    # =========================================================================
    # QUẢN LÝ PHIM
    # =========================================================================
    def show_movie_list(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Danh Sách Phim", font=("Arial", 20, "bold"), bg="white", fg="#003366").pack(pady=15)
        toolbar = tk.Frame(self.main_frame, bg="white"); toolbar.pack(fill="x", padx=20, pady=5)
        tk.Label(toolbar, text="Tìm tên phim:", bg="white").pack(side="left")
        search_var = tk.StringVar(); tk.Entry(toolbar, textvariable=search_var, width=30).pack(side="left", padx=5)
        tk.Label(toolbar, text="Lọc trạng thái:", bg="white").pack(side="left", padx=(20, 0))
        filter_combo = ttk.Combobox(toolbar, values=["Tất cả", "Đang chiếu", "Sắp chiếu"], state="readonly")
        filter_combo.current(0); filter_combo.pack(side="left", padx=5)
        
        container = tk.Frame(self.main_frame); container.pack(fill="both", expand=True, padx=20)
        tree = ttk.Treeview(container, columns=("id", "title", "year", "genre", "status"), show="headings", height=15)
        for c, h in zip(["id", "title", "year", "genre", "status"], ["ID", "Tên Phim", "Năm", "Thể Loại", "Trạng Thái"]):
            tree.heading(c, text=h); tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True)
        
        def filter_data():
            keyword = search_var.get().lower(); status_filter = filter_combo.get()
            for item in tree.get_children(): tree.delete(item)
            movies_data = self.movie_manager.get_all_movies()
            all_m = []
            if isinstance(movies_data, dict):
                for m in movies_data.get("now_showing", []): m = self.safe_data_convert(m); m['status'] = "Đang chiếu"; all_m.append(m)
                for m in movies_data.get("upcoming", []): m = self.safe_data_convert(m); m['status'] = "Sắp chiếu"; all_m.append(m)
            for m in all_m:
                if keyword in m.get("title", "").lower():
                    if status_filter == "Tất cả" or status_filter == m.get("status"):
                        tree.insert("", "end", values=(m.get("ma_phim"), m.get("title"), m.get("year"), m.get("genre"), m.get("status")))
        tk.Button(toolbar, text="Tìm kiếm", bg="#333", fg="white", command=filter_data).pack(side="left", padx=10)
        filter_data() 
        tk.Button(self.main_frame, text="Thêm Phim Mới", bg="#27AE60", fg="white", command=self.add_movie).pack(pady=15)

    def add_movie(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Thêm Phim Mới", font=("Arial", 20, "bold"), bg="white").pack(pady=15)
        form = tk.Frame(self.main_frame, bg="white"); form.pack()
        entries = {}
        fields = [("Tên phim", "title"), ("Thể loại", "genre"), ("Thời lượng (phút)", "duration"), 
                  ("Năm SX", "year"), ("Poster (File ảnh)", "poster_path")]
        for i, (lbl, key) in enumerate(fields):
            tk.Label(form, text=lbl, bg="white").grid(row=i, column=0, pady=5, sticky="e")
            e = tk.Entry(form, width=40); e.grid(row=i, column=1, pady=5, padx=10)
            entries[key] = e
        tk.Label(form, text="Mô tả:", bg="white").grid(row=5, column=0, sticky="ne")
        desc = tk.Text(form, width=40, height=5); desc.grid(row=5, column=1, pady=5, padx=10)
        v_type = tk.StringVar(value="now_showing")
        tk.Radiobutton(form, text="Đang Chiếu", variable=v_type, value="now_showing", bg="white").grid(row=6, column=0)
        tk.Radiobutton(form, text="Sắp Chiếu", variable=v_type, value="upcoming", bg="white").grid(row=6, column=1)

        def save():
            data = {k: v.get() for k, v in entries.items()}
            data["description"] = desc.get("1.0", tk.END).strip()
            data["ma_phim"] = str(uuid.uuid4())[:8]; data["rating"] = 0
            res = self.movie_manager.add_movie(data, self.admin_info, category=v_type.get())
            if "Added" in res: 
                self.log_action(self.admin_info.get("username"), f"Thêm phim: {data['title']}")
                messagebox.showinfo("OK", "Thêm phim thành công!"); self.show_movie_list()
            else: messagebox.showerror("Lỗi", res)
        tk.Button(self.main_frame, text="Lưu Phim", bg="#003366", fg="white", command=save).pack(pady=20)

    # =========================================================================
    # QUẢN LÝ GHẾ (INLINE & TO RÕ RÀNG)
    # =========================================================================
    def show_seat_list(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Quản Lý Ghế Ngồi", font=("Arial", 20, "bold"), bg="white", fg="#003366").pack(pady=10)
        
        # Toolbar
        toolbar = tk.Frame(self.main_frame, bg="white"); toolbar.pack(pady=10)
        tk.Label(toolbar, text="Chọn Rạp:", bg="white", font=("Arial", 12)).pack(side="left")
        theaters = self.theater_manager.get_all_theaters()
        t_names = [self.safe_data_convert(t).get("name") for t in theaters if self.safe_data_convert(t).get("name")]
        if not t_names: t_names = ["(Trống)"]
        selected_t = tk.StringVar(value=t_names[0])
        tk.OptionMenu(toolbar, selected_t, *t_names, command=self.render_inline_admin_map).pack(side="left", padx=10)
        
        self.map_container = tk.Frame(self.main_frame, bg="white", bd=2, relief="sunken")
        self.map_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.render_inline_admin_map(t_names[0])

    def render_inline_admin_map(self, theater_name):
        for widget in self.map_container.winfo_children(): widget.destroy()
        
        tid = None
        for t in self.theater_manager.get_all_theaters():
            t = self.safe_data_convert(t)
            if t.get("name") == theater_name: tid = t.get("theater_id"); break
        
        if not tid: 
            tk.Label(self.map_container, text="Không tìm thấy rạp", bg="white").pack(pady=20); return

        tk.Label(self.map_container, text=f"MÀN HÌNH (RẠP {tid})", bg="black", fg="white", font=("Arial", 12, "bold"), height=2).pack(fill="x", pady=(0, 20))
        legend = tk.Frame(self.map_container, bg="white"); legend.pack(pady=10)
        colors = [("Thường", "#2ECC71"), ("VIP", "#F39C12"), ("Sweetbox", "#E91E63"), ("Hỏng", "#95A5A6"), ("Đã bán", "#E74C3C")]
        for txt, clr in colors: 
            tk.Label(legend, text=f" {txt} ", bg=clr, fg="white", font=("Arial", 10, "bold"), padx=10, pady=5).pack(side="left", padx=10)
        
        # [QUAN TRỌNG] Nút Chuẩn Hóa Loại Ghế
        tk.Button(self.map_container, text="🛠 Chuẩn Hóa Loại Ghế", bg="#3498DB", fg="white", font=("Arial", 10, "bold"), 
                  command=lambda: self.fix_all_seat_colors(tid, None)).pack(pady=10)

        seat_frame = tk.Frame(self.map_container, bg="white"); seat_frame.pack(expand=True)
        seats = self.seat_manager.get_seats_by_theater(tid)
        
        for r in range(11):
            for c in range(14):
                seat_num = f"{chr(65+r)}{c+1}"
                s_obj = None
                for s in seats:
                    s = self.safe_data_convert(s)
                    if s.get("seat_number") == seat_num: s_obj = s; break
                
                row_type = "Standard"; bg_color = "#2ECC71"
                if 5 <= r <= 9: row_type = "VIP"; bg_color = "#F39C12"
                elif r == 10: row_type = "Sweetbox"; bg_color = "#E91E63"
                
                if s_obj:
                    st = s_obj.get("status")
                    if st == "broken": bg_color = "#95A5A6"
                    elif st == "occupied": bg_color = "#E74C3C"
                    elif st == "available":
                        if s_obj.get("seat_type") == "VIP": bg_color = "#F39C12"
                        elif s_obj.get("seat_type") == "Sweetbox": bg_color = "#E91E63"
                        else: bg_color = "#2ECC71"
                
                btn = tk.Button(seat_frame, text=seat_num, bg=bg_color, fg="white", font=("Arial", 9, "bold"), relief="flat", width=6, height=2)
                btn.grid(row=r, column=c, padx=3, pady=3)
                btn.config(command=lambda sn=seat_num, so=s_obj, b=btn, id=tid, rt=row_type: self.toggle_seat_status_inline(sn, so, b, id, rt))

    def toggle_seat_status_inline(self, seat_num, s_obj, btn, theater_id, row_type):
        standard_color = "#2ECC71"
        if row_type == "VIP": standard_color = "#F39C12"
        elif row_type == "Sweetbox": standard_color = "#E91E63"

        if not s_obj:
            self.seat_manager.add_seat({"seat_id": None, "theater_id": theater_id, "seat_number": seat_num, "status": "broken", "seat_type": row_type}, self.admin_info)
            btn.config(bg="#95A5A6"); return

        current_status = s_obj.get("status")
        if current_status == "available": new_st = "broken"; new_bg = "#95A5A6"
        else: new_st = "available"; new_bg = standard_color
            
        self.seat_manager.update_seat(s_obj.get("seat_id"), {"status": new_st, "seat_type": row_type}, self.admin_info)
        s_obj["status"] = new_st; s_obj["seat_type"] = row_type; btn.config(bg=new_bg)

    def fix_all_seat_colors(self, theater_id, window):
        """
        Hàm chuẩn hóa loại ghế (Standard/VIP/Sweetbox) theo hàng.
        GIỮ NGUYÊN trạng thái (Hỏng/Tốt) của ghế.
        """
        if not messagebox.askyesno("Xác nhận", "Hệ thống sẽ cập nhật lại Loại Ghế (Standard/VIP/Sweetbox) theo đúng hàng.\nTrạng thái ghế (Hỏng/Tốt) sẽ được GIỮ NGUYÊN.\nTiếp tục?"): return
        
        all_seats = self.seat_manager.get_seats_by_theater(theater_id)
        count = 0
        for s in all_seats:
            s = self.safe_data_convert(s)
            if not s: continue
            
            # Tính toán loại ghế đúng
            sn = s.get("seat_number", "A1")
            row_idx = ord(sn[0].upper()) - 65
            
            correct_type = "Standard"
            if 5 <= row_idx <= 9: correct_type = "VIP"
            elif row_idx >= 10: correct_type = "Sweetbox"
            
            # Chỉ update nếu loại ghế sai
            if s.get("seat_type") != correct_type:
                # [FIX] Chỉ update seat_type, KHÔNG update status
                self.seat_manager.update_seat(
                    s.get("seat_id"), 
                    {"seat_type": correct_type}, 
                    {"username": "System Layout Fix"}
                )
                count += 1
                
        messagebox.showinfo("Hoàn tất", f"Đã cập nhật loại ghế cho {count} ghế.")
        
        # Reload lại map
        theater_name = next((self.safe_data_convert(t).get("name") for t in self.theater_manager.get_all_theaters() if self.safe_data_convert(t).get("theater_id") == theater_id), None)
        if theater_name:
            self.render_inline_admin_map(theater_name)

    # =========================================================================
    # QUẢN LÝ VÉ (UPDATED - HIỂN THỊ STATUS)
    # =========================================================================
    def show_ticket_list(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Danh Sách Vé Đặt", font=("Arial", 20, "bold"), bg="white", fg="#003366").pack(pady=15)
        toolbar = tk.Frame(self.main_frame, bg="white"); toolbar.pack(fill="x", padx=20, pady=5)
        tk.Label(toolbar, text="Tìm:", bg="white").pack(side="left"); sv = tk.StringVar(); tk.Entry(toolbar, textvariable=sv).pack(side="left")
        
        ct = tk.Frame(self.main_frame, bg="white"); ct.pack(fill="both", expand=True, padx=20, pady=10)
        tree = ttk.Treeview(ct, columns=("id", "u", "m", "i", "p", "st"), show="headings")
        for c, h in zip(["id", "u", "m", "i", "p", "st"], ["ID", "Khách", "Phim", "Chi tiết", "Giá", "Trạng thái"]): tree.heading(c, text=h)
        tree.pack(fill="both", expand=True)
        
        def load():
            k = sv.get().lower(); ts = self.ticket_manager.get_all_tickets()[::-1]
            for i in tree.get_children(): tree.delete(i)
            for t in ts:
                t = self.safe_data_convert(t)
                if k in str(t.get("ticket_id")).lower() or k in str(t.get("username")).lower():
                    ss = ','.join(t.get('seats', [])) if isinstance(t.get('seats'), list) else str(t.get('seats'))
                    st = t.get("status", "valid").upper()
                    tree.insert("", "end", values=(t.get("ticket_id"), t.get("username"), t.get("movie_title"), 
                                                   f"{t.get('date')} {t.get('show_time')} ({ss})", 
                                                   f"{t.get('price'):,}", st))
        tk.Button(toolbar, text="Tìm", command=load).pack(side="left", padx=10); load()
        
        def cancel_ticket():
            sel = tree.selection()
            if not sel: return messagebox.showwarning("Lỗi", "Chọn vé để hủy")
            tid = tree.item(sel)['values'][0]
            if messagebox.askyesno("Xác nhận", "Hủy vé này? (Doanh thu sẽ bị trừ)"):
                res = self.ticket_manager.delete_ticket(tid)
                messagebox.showinfo("KQ", res); load()
                
        tk.Button(self.main_frame, text="Hủy Vé Đã Chọn", bg="#C0392B", fg="white", command=cancel_ticket).pack(pady=10)

    # =========================================================================
    # QUẢN LÝ THÔNG TIN KHÁC (USER, NEWS, THEATER, SHOWTIME)
    # =========================================================================
    def show_user_list(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Danh Sách Người Dùng", font=("Arial", 20, "bold"), bg="white").pack(pady=15)
        toolbar = tk.Frame(self.main_frame, bg="white"); toolbar.pack(fill="x", padx=20, pady=5)
        tk.Label(toolbar, text="Tìm Username/Email:", bg="white").pack(side="left")
        search_var = tk.StringVar(); tk.Entry(toolbar, textvariable=search_var, width=30).pack(side="left", padx=5)
        container = tk.Frame(self.main_frame); container.pack(fill="both", expand=True, padx=20)
        tree = ttk.Treeview(container, columns=("u", "n", "e", "t"), show="headings")
        for c, h in zip(["u", "n", "e", "t"], ["Username", "Họ Tên", "Email", "Loại TK"]): tree.heading(c, text=h)
        tree.pack(fill="both", expand=True)
        def search_users():
            keyword = search_var.get().lower(); 
            for item in tree.get_children(): tree.delete(item)
            for u in self.auth_manager.get_all_users():
                u = self.safe_data_convert(u)
                if keyword in u.get("username", "").lower() or keyword in u.get("email", "").lower():
                    tree.insert("", "end", values=(u.get("username"), u.get("full_name"), u.get("email"), u.get("type")))
        tk.Button(toolbar, text="Tìm", bg="#333", fg="white", command=search_users).pack(side="left", padx=10); search_users()
        def view_user_history(event):
            sel = tree.selection()
            if not sel: return
            username = tree.item(sel)['values'][0]; win = tk.Toplevel(self); win.title(f"Lịch sử vé của: {username}"); win.geometry("600x400")
            tk.Label(win, text=f"Vé đã mua của {username}", font=("Arial", 14, "bold")).pack(pady=10)
            cols = ("mov", "date", "price"); t_tree = ttk.Treeview(win, columns=cols, show="headings")
            t_tree.heading("mov", text="Phim"); t_tree.heading("date", text="Ngày"); t_tree.heading("price", text="Giá")
            t_tree.pack(fill="both", expand=True)
            try:
                if hasattr(self.ticket_manager, 'get_tickets_by_username'):
                    tickets = self.ticket_manager.get_tickets_by_username(username)
                    for t in tickets:
                        t_title = t.movie_title if hasattr(t, 'movie_title') else t.get('movie_title')
                        t_date = t.date if hasattr(t, 'date') else t.get('date')
                        t_time = t.show_time if hasattr(t, 'show_time') else t.get('show_time')
                        t_price = t.price if hasattr(t, 'price') else t.get('price')
                        t_tree.insert("", "end", values=(t_title, f"{t_date} {t_time}", f"{t_price:,}"))
            except: pass
        tree.bind("<Double-1>", view_user_history)
        tk.Label(self.main_frame, text="(Double-click vào dòng để xem lịch sử mua vé)", bg="white", fg="gray").pack(pady=5)

    def show_news_list(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Danh Sách Tin Tức", font=("Arial", 20, "bold"), bg="white").pack(pady=15)
        container = tk.Frame(self.main_frame); container.pack(fill="both", expand=True, padx=20)
        tree = ttk.Treeview(container, columns=("t", "a", "d"), show="headings")
        tree.heading("t", text="Tiêu đề"); tree.column("t", width=300); tree.heading("a", text="Người đăng"); tree.heading("d", text="Ngày")
        tree.pack(fill="both", expand=True)
        for n in self.news_manager.get_all_news():
            n = self.safe_data_convert(n)
            if n: tree.insert("", "end", values=(n.get("title"), n.get("admin_username"), n.get("created_at")))
        tk.Button(self.main_frame, text="Thêm Tin", bg="#003366", fg="white", command=self.add_news).pack(pady=15)

    def add_news(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Đăng Tin Mới", font=("Arial", 18, "bold"), bg="white").pack(pady=10)
        f = tk.Frame(self.main_frame, bg="white"); f.pack()
        tk.Label(f, text="Tiêu đề:", bg="white").pack(anchor="w"); e_title = tk.Entry(f, width=50); e_title.pack(pady=5)
        tk.Label(f, text="Nội dung:", bg="white").pack(anchor="w"); t_content = tk.Text(f, width=50, height=10); t_content.pack(pady=5)
        def save():
            t = e_title.get(); c = t_content.get("1.0", tk.END).strip()
            if t and c:
                self.news_manager.add_news(t, c, self.admin_info.get("username"), self.admin_info)
                self.log_action(self.admin_info.get("username"), f"Đăng tin: {t}")
                messagebox.showinfo("OK", "Đã đăng tin!"); self.show_news_list()
            else: messagebox.showerror("Lỗi", "Nhập đủ thông tin")
        tk.Button(self.main_frame, text="Đăng", bg="#27AE60", fg="white", command=save).pack(pady=20)

    def show_cinema_info(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Thông Tin Rạp", font=("Arial", 20, "bold"), bg="white").pack(pady=20)
        tk.Label(self.main_frame, text="Duo Cinema Center\nĐịa chỉ: 123 Đường ABC, TP.HCM\nHotline: 1900 1000", bg="white", font=("Arial", 12)).pack()

    def show_theater_list(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Danh Sách Phòng Chiếu", font=("Arial", 20, "bold"), bg="white").pack(pady=15)
        container = tk.Frame(self.main_frame); container.pack(fill="both", expand=True, padx=20)
        tree = ttk.Treeview(container, columns=("id", "name", "cap"), show="headings")
        tree.heading("id", text="ID"); tree.heading("name", text="Tên Phòng"); tree.heading("cap", text="Sức Chứa")
        tree.pack(fill="both", expand=True)
        for t in self.theater_manager.get_all_theaters():
            t = self.safe_data_convert(t)
            if t: tree.insert("", "end", values=(t.get("theater_id"), t.get("name"), t.get("capacity")))
        tk.Button(self.main_frame, text="Thêm Phòng", bg="#003366", fg="white", command=self.add_theater).pack(pady=10)

    def add_theater(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Thêm Phòng Chiếu", font=("Arial", 18, "bold"), bg="white").pack(pady=10)
        f = tk.Frame(self.main_frame, bg="white"); f.pack()
        e_id = tk.Entry(f); e_name = tk.Entry(f); e_cap = tk.Entry(f)
        tk.Label(f, text="Mã Phòng (VD: THEATER01):", bg="white").grid(row=0, column=0); e_id.grid(row=0, column=1)
        tk.Label(f, text="Tên Phòng:", bg="white").grid(row=1, column=0); e_name.grid(row=1, column=1)
        tk.Label(f, text="Sức Chứa:", bg="white").grid(row=2, column=0); e_cap.grid(row=2, column=1)
        def save():
            d = {"theater_id": e_id.get(), "name": e_name.get(), "capacity": e_cap.get(), "status": "Active"}
            res = self.theater_manager.add_theater(d)
            if "Added" in res: 
                self.log_action(self.admin_info.get("username"), f"Thêm rạp: {d['name']}"); self.show_theater_list()
            messagebox.showinfo("Thông báo", res)
        tk.Button(self.main_frame, text="Lưu", bg="#27AE60", fg="white", command=save).pack(pady=20)

    def show_showtime_list(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Danh Sách Suất Chiếu", font=("Arial", 20, "bold"), bg="white").pack(pady=10)
        container = tk.Frame(self.main_frame); container.pack(fill="both", expand=True, padx=20)
        tree = ttk.Treeview(container, columns=("id", "mov", "time", "date"), show="headings")
        for c, t in zip(["id", "mov", "time", "date"], ["ID", "Phim", "Giờ", "Ngày"]): tree.heading(c, text=t)
        tree.pack(fill="both", expand=True)
        for s in self.showtime_manager.get_all_showtimes():
            s = self.safe_data_convert(s)
            if s: tree.insert("", "end", values=(s.get("showtime_id"), s.get("movie_title"), s.get("show_time"), s.get("date")))
        tk.Button(self.main_frame, text="Thêm Suất Chiếu", bg="#003366", fg="white", command=self.add_showtime).pack(pady=10)

    def add_showtime(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Thêm Suất Chiếu Mới", font=("Arial", 18, "bold"), bg="white").pack(pady=10)
        f = tk.Frame(self.main_frame, bg="white"); f.pack()
        
        movies = self.movie_manager.get_all_movies()
        movie_titles = []
        if isinstance(movies, dict):
            for m in movies.get("now_showing", []): movie_titles.append(self.safe_data_convert(m).get("title"))
            for m in movies.get("upcoming", []): movie_titles.append(self.safe_data_convert(m).get("title"))
        
        theaters = self.theater_manager.get_all_theaters()
        theater_ids = [self.safe_data_convert(t).get("theater_id") for t in theaters]

        tk.Label(f, text="Phim:", bg="white").grid(row=0, column=0); cb_mov = ttk.Combobox(f, values=movie_titles, state="readonly"); cb_mov.grid(row=0, column=1)
        tk.Label(f, text="Giờ (HH:MM):", bg="white").grid(row=1, column=0); e_time = tk.Entry(f); e_time.grid(row=1, column=1)
        tk.Label(f, text="Ngày (DD-MM-YYYY):", bg="white").grid(row=2, column=0); e_date = tk.Entry(f); e_date.grid(row=2, column=1)
        tk.Label(f, text="Phòng Chiếu:", bg="white").grid(row=3, column=0); cb_tid = ttk.Combobox(f, values=theater_ids, state="readonly"); cb_tid.grid(row=3, column=1)
        
        def save():
            d = {"showtime_id": str(uuid.uuid4())[:6], "movie_title": cb_mov.get(), "show_time": e_time.get(), "date": e_date.get(), "theater_id": cb_tid.get()}
            self.showtime_manager.add_showtime(d, self.admin_info)
            self.log_action(self.admin_info.get("username"), f"Thêm suất chiếu: {d['movie_title']} - {d['show_time']}")
            messagebox.showinfo("OK", "Đã thêm suất chiếu"); self.show_showtime_list()
        tk.Button(self.main_frame, text="Lưu", bg="#27AE60", fg="white", command=save).pack(pady=20)

    # --- Thông tin Admin & Log ---
    def show_admin_info(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Thông Tin Cá Nhân", font=("Arial", 22, "bold"), bg="white", fg="#003366").pack(pady=30)
        info_frame = tk.Frame(self.main_frame, bg="white"); info_frame.pack(pady=10)
        try:
            curr = self.auth_manager.get_user_by_username(self.admin_info.get("username"))
            if curr: self.admin_info = self.safe_data_convert(curr)
        except: pass
        fields = [("Tên đăng nhập:", "username", False), ("Chức vụ:", "type", False), ("Họ và Tên:", "full_name", True),     
                  ("Email:", "email", True), ("Số điện thoại:", "phone", True), ("Địa chỉ:", "address", True)]
        self.profile_entries = {} 
        for i, (label, key, edit) in enumerate(fields):
            tk.Label(info_frame, text=label, font=("Arial", 12, "bold"), bg="white").grid(row=i, column=0, sticky="e", padx=20, pady=10)
            entry = tk.Entry(info_frame, width=40, font=("Arial", 11))
            entry.grid(row=i, column=1, sticky="w", padx=10, pady=10)
            entry.insert(0, str(self.admin_info.get(key, "")))
            if not edit: entry.config(state="readonly", fg="gray")
            else: self.profile_entries[key] = entry 
        tk.Button(self.main_frame, text="Lưu Thay Đổi", bg="#27AE60", fg="white", font=("Arial", 12, "bold"), command=self.save_admin_profile).pack(pady=30)

    def save_admin_profile(self):
        new_data = {k: v.get() for k, v in self.profile_entries.items()}
        try:
            self.auth_manager.update_user(self.admin_info.get("username"), new_data)
            self.admin_info.update(new_data)
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin!")
            self.show_admin_info()
        except Exception as e: messagebox.showerror("Lỗi", f"Lỗi: {e}")

    def show_audit_logs(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Nhật Ký Hoạt Động", font=("Arial", 22, "bold"), bg="white", fg="#003366").pack(pady=15)
        container = tk.Frame(self.main_frame); container.pack(fill="both", expand=True, padx=20)
        tree = ttk.Treeview(container, columns=("t", "a", "ac"), show="headings")
        tree.heading("t", text="Thời gian"); tree.heading("a", text="Người dùng"); tree.heading("ac", text="Hành động")
        tree.pack(fill="both", expand=True)
        log_file = os.path.join(project_root, "data", "audit_logs.json")
        if os.path.exists(log_file):
            try: 
                with open(log_file, "r", encoding="utf-8") as f: 
                    for l in json.load(f):
                        l = self.safe_data_convert(l)
                        tree.insert("", "end", values=(l.get("time"), l.get("actor"), l.get("action")))
            except: pass