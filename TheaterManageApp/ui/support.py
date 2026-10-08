import tkinter as tk
import os
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from controllers.movie_manager import MovieManager
def create_footer(self):
        """Tạo phần footer (Download App)"""
        footer_frame = tk.Frame(self.main_container, bg="#003087")
        footer_frame.pack(fill="x", pady=20)

        content_frame = tk.Frame(footer_frame, bg="#003087")
        content_frame.pack(fill="x", padx=50)

        # Phone Image
        try:
            phone_img = Image.open("images/phone.png")
            phone_img = phone_img.resize((200, 300), Image.LANCZOS)
            self.phone = ImageTk.PhotoImage(phone_img)
            tk.Label(content_frame, image=self.phone, bg="#003087").pack(side="left", padx=20)
        except FileNotFoundError:
            tk.Label(content_frame, text="Phone Image", font=("Arial", 12), fg="white", bg="#003087").pack(side="left", padx=20)

        # Text and QR Code
        text_frame = tk.Frame(content_frame, bg="#003087")
        text_frame.pack(side="left", fill="x", expand=True)

        tk.Label(text_frame, text="Đặt Vé Online - Không Lo Trễ Nãi", font=("Arial", 16, "bold"), fg="white", bg="#003087").pack(anchor="w")
        tk.Label(text_frame, text="Ghét đông đúc ở quầy? Lỡ xuất hàng mua vé? Hãy quên đi cách mua vé giấy truyền thống, thông tin thời gian hay kết hợp lịch vé online phiên toại.", 
                 font=("Arial", 12), fg="white", bg="#003087", wraplength=600).pack(anchor="w", pady=5)

        qr_frame = tk.Frame(content_frame, bg="#003087")
        qr_frame.pack(side="right", padx=20)

        try:
            qr_img = Image.open("images/qr_code.png")
            qr_img = qr_img.resize((100, 100), Image.LANCZOS)
            self.qr_code = ImageTk.PhotoImage(qr_img)
            tk.Label(qr_frame, image=self.qr_code, bg="#003087").pack()
        except FileNotFoundError:
            tk.Label(qr_frame, text="QR Code", font=("Arial", 12), fg="white", bg="#003087").pack()

        download_frame = tk.Frame(qr_frame, bg="#003087")
        download_frame.pack(pady=10)

        try:
            app_store_img = Image.open("images/app_store.png")
            app_store_img = app_store_img.resize((120, 40), Image.LANCZOS)
            self.app_store = ImageTk.PhotoImage(app_store_img)
            tk.Button(download_frame, image=self.app_store, bg="#003087", borderwidth=0).pack(side="left", padx=5)
        except FileNotFoundError:
            tk.Button(download_frame, text="App Store", font=("Arial", 10), fg="white", bg="#003087").pack(side="left", padx=5)

        try:
            google_play_img = Image.open("images/google_play.png")
            google_play_img = google_play_img.resize((120, 40), Image.LANCZOS)
            self.google_play = ImageTk.PhotoImage(google_play_img)
            tk.Button(download_frame, image=self.google_play, bg="#003087", borderwidth=0).pack(side="left", padx=5)
        except FileNotFoundError:
            tk.Button(download_frame, text="Google Play", font=("Arial", 10), fg="white", bg="#003087").pack(side="left", padx=5)
