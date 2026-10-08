import tkinter as tk
from tkinter import messagebox
import sys
import os
import ctypes

# --- Cấu hình đường dẫn dự án ---
project_root = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    # Chạy từ file .exe (PyInstaller): data/ và images/ nằm trong thư mục _internal
    project_root = sys._MEIPASS
os.chdir(project_root)  # Luôn đọc data/ trong thư mục dự án dù chạy từ đâu
if project_root not in sys.path:
    sys.path.append(project_root)

# --- FIX LỖI DPI (Đặt ngay tại đây để đồng bộ toàn app) ---
try:
    # Báo cho Windows biết app này hỗ trợ độ phân giải cao
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# --- Import các module nội bộ ---
try:
    from ui.login_ui import Login 
except ImportError as e:
    print(f"Lỗi Import: {e}")
    # sys.exit(1) # Comment lại để debug nếu cần

# Biến toàn cục quản lý timer
global auto_switch_id
auto_switch_id = None

def show_intro_screen(root_window):
    """Hiển thị màn hình giới thiệu (Splash Screen)"""
    global auto_switch_id
    
    root_window.withdraw() 
    
    intro_root = tk.Toplevel(root_window)
    intro_root.title("Chào mừng!")
    
    # --- TỰ ĐỘNG TÍNH TOÁN TỶ LỆ SCALE ---
    try:
        # Lấy mật độ điểm ảnh (DPI) hiện tại. Chuẩn là 96.
        # Nếu màn hình scale 125% -> dpi ~ 120. Scale factor = 1.25
        dpi = root_window.winfo_fpixels('1i')
        scale_factor = dpi / 96.0
    except:
        scale_factor = 1.0

    # Kích thước gốc mong muốn
    BASE_WIDTH = 550
    BASE_HEIGHT = 400

    # Kích thước thực tế sau khi nhân với tỷ lệ scale
    window_width = int(BASE_WIDTH * scale_factor)
    window_height = int(BASE_HEIGHT * scale_factor)
    
    # Lấy kích thước màn hình
    screen_width = intro_root.winfo_screenwidth()
    screen_height = intro_root.winfo_screenheight()
    
    # Tính tọa độ trung tâm
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    
    intro_root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    intro_root.overrideredirect(True) 

    # --- Màu sắc ---
    PRIMARY_COLOR = "#E74C3C"
    BG_COLOR = "#2C3E50"      
    TEXT_COLOR = "#ECF0F1"    
    ACCENT_COLOR = "#F1C40F"  

    intro_root.configure(bg=BG_COLOR)
    intro_root.resizable(False, False)

    # --- UI Components ---
    main_frame = tk.Frame(intro_root, bg=BG_COLOR)
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)

    # Icon (Tăng size font theo scale nếu cần, nhưng thường font tự scale)
    icon_label = tk.Label(
        main_frame, text="🍿", font=("Arial", int(60 * scale_factor * 0.8)), # Giảm nhẹ hệ số font chút cho đẹp
        bg=BG_COLOR, fg=ACCENT_COLOR
    )
    icon_label.pack(pady=(0, 10))

    title_label = tk.Label(
        main_frame, text="CINEMA MANAGEMENT APP",
        font=("Arial", 24, "bold"), fg=PRIMARY_COLOR, bg=BG_COLOR
    )
    title_label.pack(pady=(0, 5))
    
    description_label = tk.Label(
        main_frame,
        text="Trải nghiệm đặt vé xem phim tuyệt vời nhất trong tầm tay bạn.\n"
             "Khám phá các bộ phim mới nhất, xem lịch chiếu và chọn ghế dễ dàng.",
        font=("Arial", 11, "italic"), fg=TEXT_COLOR, bg=BG_COLOR,
        wraplength=int(500 * scale_factor), justify=tk.CENTER
    )
    description_label.pack(pady=(10, 30))
    
    login_button = tk.Button(
        main_frame,
        text="BẮT ĐẦU >",
        font=("Arial", 12, "bold"),
        fg=BG_COLOR, bg=ACCENT_COLOR,
        activebackground=PRIMARY_COLOR, activeforeground="white",
        relief=tk.FLAT, padx=15, pady=8, 
        cursor="hand2",
        command=lambda: switch_to_main_app(intro_root, root_window)
    )
    login_button.pack(pady=10)
    
    footer_label = tk.Label(
        intro_root, text="Đang tải dữ liệu...",
        font=("Arial", 9), fg=TEXT_COLOR, bg=BG_COLOR
    )
    footer_label.pack(side=tk.BOTTOM, pady=10)

    auto_switch_id = intro_root.after(3000, lambda: switch_to_main_app(intro_root, root_window))
    
    return intro_root

def switch_to_main_app(intro_root, root_main):
    """Chuyển sang màn hình chính"""
    global auto_switch_id

    if auto_switch_id:
        try:
            intro_root.after_cancel(auto_switch_id)
            auto_switch_id = None
        except Exception: pass

    try: intro_root.destroy()
    except tk.TclError: pass
    
    root_main.deiconify() 
    
    if not hasattr(root_main, 'app_initialized'):
        root_main.title("Movie Ticket Booking System - Login")
        
        # --- Căn giữa Login Window (Cũng cần tính scale) ---
        try:
            scale = root_main.winfo_fpixels('1i') / 96.0
        except: scale = 1.0
            
        base_w, base_h = 980, 500
        w = int(base_w * scale)
        h = int(base_h * scale)
        
        sw = root_main.winfo_screenwidth()
        sh = root_main.winfo_screenheight()
        x = int(sw/2 - w/2)
        y = int(sh/2 - h/2)
        
        # Lưu ý: Login class bên trong cũng có lệnh geometry, 
        # nhưng ta set trước ở đây cho root để tránh giật hình
        root_main.geometry(f"{w}x{h}+{x}+{y}")
        root_main.configure(bg="#fff")
        
        try:
            app = Login(root_main)
            root_main.app_initialized = True
        except Exception as e:
            messagebox.showerror("Lỗi Khởi Động", f"Không thể tải màn hình đăng nhập:\n{e}")
            root_main.destroy()

def main():
    root = tk.Tk()
    # Ẩn root ngay lập tức để tránh hiện cửa sổ trắng nhỏ
    root.withdraw()
    show_intro_screen(root)
    root.mainloop()

if __name__ == "__main__":
    main()