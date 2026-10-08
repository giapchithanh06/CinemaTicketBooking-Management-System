import tkinter as tk
from tkinter import messagebox
import sys
import os


project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)  # Luôn đọc data/ trong thư mục dự án dù chạy từ đâu
if project_root not in sys.path:
    sys.path.append(project_root)

from services.api_crawler import MovieCrawler 
from ui.login_ui import Login # Đảm bảo import lớp Login
# ... các lệnh import khác

global auto_switch_id

def show_intro_screen(root_window):

    global auto_switch_id
    
    root_window.withdraw() 
    
    intro_root = tk.Toplevel(root_window)
    intro_root.title("Chào mừng!")
    
    # --- Cấu hình Kích thước và Vị trí ---
    WINDOW_WIDTH = 550
    WINDOW_HEIGHT = 400
    screen_width = intro_root.winfo_screenwidth()
    screen_height = intro_root.winfo_screenheight()
    center_x = int(screen_width/2 - WINDOW_WIDTH/2)
    center_y = int(screen_height/2 - WINDOW_HEIGHT/2)
    intro_root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{center_x}+{center_y}')
    
    intro_root.overrideredirect(True) 

    PRIMARY_COLOR = "#E74C3C"
    BG_COLOR = "#2C3E50"      
    TEXT_COLOR = "#ECF0F1"    
    ACCENT_COLOR = "#F1C40F"  

    intro_root.configure(bg=BG_COLOR)
    intro_root.resizable(False, False)

    main_frame = tk.Frame(intro_root, bg=BG_COLOR)
    main_frame.pack(expand=True, padx=40, pady=40)

    icon_label = tk.Label(
        main_frame,
        text="🍿",
        font=("Arial", 60),
        bg=BG_COLOR,
        fg=ACCENT_COLOR
    )
    icon_label.pack(pady=(0, 10))

    title_label = tk.Label(
        main_frame,
        text="CINEMA BOOKING APP",
        font=("Arial", 28, "bold"),
        fg=PRIMARY_COLOR,
        bg=BG_COLOR
    )
    title_label.pack(pady=(0, 5))
    
    description_label = tk.Label(
        main_frame,
        text="Trải nghiệm đặt vé xem phim tuyệt vời nhất trong tầm tay bạn.\nKhám phá các bộ phim mới nhất, xem lịch chiếu và chọn ghế dễ dàng.",
        font=("Arial", 11, "italic"),
        fg=TEXT_COLOR,
        bg=BG_COLOR,
        wraplength=500, # Giúp giới hạn chiều rộng của văn bản
        justify=tk.CENTER
    )
    description_label.pack(pady=(10, 30))
    
    login_button = tk.Button(
        main_frame,
        text="BẮT ĐẦU ĐẶT VÉ >",
        font=("Arial", 14, "bold"),
        fg=BG_COLOR,
        bg=ACCENT_COLOR,
        activebackground=PRIMARY_COLOR, 
        activeforeground="white",
        relief=tk.FLAT,
        padx=15, 
        pady=8, 
        command=lambda: switch_to_main_app(intro_root, root_window)
    )
    login_button.pack(pady=10)
    
    footer_label = tk.Label(
        intro_root,
        text="Đang tải dữ liệu...",
        font=("Arial", 9),
        fg=TEXT_COLOR,
        bg=BG_COLOR
    )
    footer_label.pack(side=tk.BOTTOM, pady=10)

    auto_switch_id = intro_root.after(3000, lambda: switch_to_main_app(intro_root, root_window))
    
    return intro_root

def switch_to_main_app(intro_root, root_main):

    global auto_switch_id

    try:
        intro_root.after_cancel(auto_switch_id)
    except Exception:
        pass

    intro_root.destroy()
    
    root_main.deiconify() 
    
    if not hasattr(root_main, 'app_initialized'):
        root_main.title("Movie Ticket Booking System - Login")
    
        root_main.geometry("800x600") 
        root_main.configure(bg="#fff")
        
        app = Login(root_main)
        
        root_main.app_initialized = True


def main():

    root = tk.Tk()
    
    show_intro_screen(root)

    root.mainloop()

if __name__ == "__main__":
    main()