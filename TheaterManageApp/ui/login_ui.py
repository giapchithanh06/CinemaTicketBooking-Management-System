import re
import os
import sys
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk

# --- Cấu hình đường dẫn ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import AuthManager
try:
    from controllers.auth_manager import AuthManager
except ImportError as e:
    messagebox.showerror("Lỗi", f"Missing AuthManager: {e}")
    sys.exit(1)

class Login:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Duo Cinema")
        
        w, h = 900, 500
        ws, hs = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f'{w}x{h}+{int((ws/2)-(w/2))}+{int((hs/2)-(h/2))}')
        self.root.resizable(False, False)

        try: self.auth_manager = AuthManager()
        except: self.auth_manager = None

        self.load_resources()
        self.setup_ui()

    def load_resources(self):
        img_dir = os.path.join(project_root, "images")
        def safe_load(name):
            p = os.path.join(img_dir, name)
            if os.path.exists(p): return ImageTk.PhotoImage(Image.open(p))
            return None
        def safe_load_resize(name):
            p = os.path.join(img_dir, name)
            if os.path.exists(p): return ImageTk.PhotoImage(Image.open(p).resize((20, 20)))
            return None
        self.login_img = safe_load("login.png")
        self.eye_icon = safe_load_resize("eye.png")
        self.eye_off_icon = safe_load_resize("eye_off.png")

    def setup_ui(self):
        if self.login_img: Label(self.root, image=self.login_img, bg='white').place(x=50, y=50)
        
        Frame_Login = Frame(self.root, bg='white')
        Frame_Login.place(x=500, y=50, width=400, height=400)

        Label(Frame_Login, text='Sign in', fg='#57a1f8', bg='white', 
              font=('Microsoft YaHei UI Light', 23, 'bold')).place(x=100, y=20)

        # Email
        self.user = Entry(Frame_Login, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.user.place(x=30, y=80); self.user.insert(0, 'Email')
        self.user.bind('<FocusIn>', self.on_enter_user); self.user.bind('<FocusOut>', self.on_leave_user)
        Frame(Frame_Login, width=295, height=2, bg='black').place(x=25, y=107)

        # Password
        self.code = Entry(Frame_Login, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.code.place(x=30, y=150); self.code.insert(0, 'Password')
        self.code.bind('<FocusIn>', self.on_enter_pw); self.code.bind('<FocusOut>', self.on_leave_pw)
        Frame(Frame_Login, width=295, height=2, bg='black').place(x=25, y=177)

        self.show_password = BooleanVar(value=False)
        self.toggle_btn = Button(Frame_Login, image=self.eye_off_icon, bg='white', border=0, cursor='hand2', command=self.toggle_pw)
        if self.eye_off_icon: self.toggle_btn.place(x=320, y=150)

        # Sign In Button
        Button(Frame_Login, width=39, pady=7, text='Sign in', bg='#57a1f8', fg='white', border=0, cursor='hand2', command=self.signin).place(x=25, y=204)
        
        # --- NÚT QUÊN MẬT KHẨU (MỚI) ---
        forgot_btn = Button(Frame_Login, text="Forgot Password?", border=0, bg='white', fg='#57a1f8',
                            font=('Microsoft YaHei UI Light', 9), cursor='hand2', command=self.show_forgot_password)
        forgot_btn.place(x=25, y=250)

        # Sign Up Link
        Label(Frame_Login, text="Don't have an account?", fg='black', bg='white', font=('Microsoft YaHei UI Light', 9)).place(x=70, y=280)
        Button(Frame_Login, width=6, text='Sign up', border=0, bg='white', cursor='hand2', fg='#57a1f8', command=self.go_to_signup).place(x=235, y=278)

    # --- LOGIC QUÊN MẬT KHẨU ---
    def show_forgot_password(self):
        """Hiển thị Popup Reset Password"""
        win = Toplevel(self.root)
        win.title("Reset Password")
        win.geometry("400x350")
        win.configure(bg="white")
        
        # Căn giữa popup so với cửa sổ chính
        x = self.root.winfo_x() + 300
        y = self.root.winfo_y() + 80
        win.geometry(f"+{x}+{y}")

        Label(win, text="Khôi Phục Mật Khẩu", font=("Arial", 16, "bold"), bg="white", fg="#57a1f8").pack(pady=20)
        
        def create_field(label_text):
            Label(win, text=label_text, bg="white", font=("Arial", 10)).pack(anchor="w", padx=40)
            e = Entry(win, width=35, bd=1, relief="solid", font=("Arial", 11))
            e.pack(pady=(0, 10))
            return e

        # Chỉ cần Email và SĐT
        e_entry = create_field("Email đã đăng ký:")
        p_entry = create_field("Số điện thoại:")
        new_pass_entry = create_field("Mật khẩu mới:")
        new_pass_entry.config(show="*")

        def submit_reset():
            email = e_entry.get()
            phone = p_entry.get()
            new_pass = new_pass_entry.get()

            if not all([email, phone, new_pass]):
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!", parent=win)
                return

            if len(new_pass) < 6:
                messagebox.showerror("Lỗi", "Mật khẩu phải từ 6 ký tự trở lên!", parent=win)
                return

            # Gọi AuthManager xác thực
            success, msg = self.auth_manager.reset_password(email, phone, new_pass)
            
            if success:
                messagebox.showinfo("Thành công", msg, parent=win)
                win.destroy()
            else:
                messagebox.showerror("Thất bại", msg, parent=win)

        Button(win, text="Xác Nhận", bg="#57a1f8", fg="white", font=("Arial", 11, "bold"), 
               width=20, command=submit_reset).pack(pady=10)

    # --- Các hàm cũ giữ nguyên ---
    def on_enter_user(self, e): 
        if self.user.get() == 'Email': self.user.delete(0, 'end')
    def on_leave_user(self, e): 
        if not self.user.get(): self.user.insert(0, 'Email')
    def on_enter_pw(self, e):
        if self.code.get() == 'Password':
            self.code.delete(0, 'end')
            if not self.show_password.get(): self.code.config(show="*")
    def on_leave_pw(self, e):
        if not self.code.get():
            self.code.config(show=""); self.code.insert(0, 'Password')

    def toggle_pw(self):
        if self.code.get() == 'Password': return
        if self.show_password.get():
            self.code.config(show="*")
            if self.eye_off_icon: self.toggle_btn.config(image=self.eye_off_icon)
            self.show_password.set(False)
        else:
            self.code.config(show="")
            if self.eye_icon: self.toggle_btn.config(image=self.eye_icon)
            self.show_password.set(True)

    def signin(self):
        email = self.user.get()
        password = self.code.get()
        if email == 'Email' or password == 'Password':
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
        try:
            res = self.auth_manager.login(email, password)
            if "successful" in res.lower():
                u = self.auth_manager.get_current_user()
                if u.get("type") == "Admin": self.open_admin_ui(u)
                else: self.open_user_ui(u)
            else: messagebox.showerror("Lỗi", res)
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def open_admin_ui(self, u):
        try:
            from ui.admin_ui import AdminDashboard; self.root.destroy(); app = AdminDashboard(u); app.mainloop()
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def open_user_ui(self, u):
        try:
            from ui.user_ui import UserUI; self.root.destroy(); root = Tk(); UserUI(root, u); root.mainloop()
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def go_to_signup(self):
        try:
            from ui.sign_up import SignUp; self.root.destroy(); root = Tk(); SignUp(root); root.mainloop()
        except: pass