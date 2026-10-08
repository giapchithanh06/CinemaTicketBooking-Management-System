import re
import os
import sys
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
from tkcalendar import DateEntry

# --- Xử lý đường dẫn import ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from controllers.auth_manager import AuthManager
except ImportError:
    messagebox.showerror("Lỗi", "Không tìm thấy module AuthManager")
    sys.exit(1)

class SignUp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sign Up")
        self.root.configure(bg="#fff")

        # --- Cấu hình vị trí ---
        window_width = 980
        window_height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        pos_x = (screen_width // 2) - (window_width // 2)
        pos_y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f'{window_width}x{window_height}+{pos_x}+{pos_y}')
        self.root.resizable(False, False)

        # Initialize AuthManager
        try:
            self.auth_manager = AuthManager()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi kết nối dữ liệu: {e}")
            self.auth_manager = None

        # --- Tải tài nguyên ---
        self.load_resources()

        # --- Giao diện ---
        # Ảnh bên trái
        if self.signup_img:
            Label(self.root, image=self.signup_img, bg='white').place(x=50, y=50)
        
        Frame_SignUp = Frame(self.root, bg='white')
        Frame_SignUp.place(x=500, y=50, width=400, height=600)

        heading = Label(Frame_SignUp, text='Sign Up', fg='#57a1f8', bg='white', 
                        font=('Microsoft YaHei UI Light', 23, 'bold'))
        heading.place(x=100, y=20)

        # --- Tạo các ô nhập liệu (Refactored) ---
        self.username = self.create_entry(Frame_SignUp, 70, 'Username')
        self.name = self.create_entry(Frame_SignUp, 120, 'Full Name')
        self.email = self.create_entry(Frame_SignUp, 170, 'Email')
        self.phone = self.create_entry(Frame_SignUp, 220, 'Phone Number')

        # --- Gender Selection ---
        Label(Frame_SignUp, text='Gender:', fg='black', bg='white', 
              font=('Microsoft YaHei UI Light', 11)).place(x=30, y=270)
        self.gender = StringVar(value='Nam')
        Radiobutton(Frame_SignUp, text='Nam', variable=self.gender, value='Nam', 
                    bg='white', font=('Microsoft YaHei UI Light', 9)).place(x=100, y=270)
        Radiobutton(Frame_SignUp, text='Nữ', variable=self.gender, value='Nữ', 
                    bg='white', font=('Microsoft YaHei UI Light', 9)).place(x=160, y=270)
        Radiobutton(Frame_SignUp, text='Khác', variable=self.gender, value='Khác', 
                    bg='white', font=('Microsoft YaHei UI Light', 9)).place(x=220, y=270)

        # --- Date of Birth ---
        Label(Frame_SignUp, text='Date of Birth:', fg='black', bg='white', 
              font=('Microsoft YaHei UI Light', 11)).place(x=30, y=310)
        self.dob = DateEntry(Frame_SignUp, width=20, background='#57a1f8', 
                             foreground='white', borderwidth=0, date_pattern='dd-mm-yyyy')
        self.dob.place(x=120, y=310)

        # --- Password Entries ---
        self.code = self.create_password_entry(Frame_SignUp, 350, 'Password', 'toggle_pw')
        self.confirm_code = self.create_password_entry(Frame_SignUp, 400, 'Confirm Password', 'toggle_cpw')

        # --- Terms Checkbox ---
        self.terms = BooleanVar(value=False)
        Checkbutton(Frame_SignUp, text='I agree to the Terms of Service', variable=self.terms, 
                    bg='white', font=('Microsoft YaHei UI Light', 9)).place(x=30, y=450)

        # --- Buttons ---
        sign_up = Button(Frame_SignUp, width=39, pady=7, text='Sign Up', bg='#57a1f8', 
                         fg='white', border=0, command=self.signup)
        sign_up.place(x=35, y=490)

        login_link = Button(Frame_SignUp, text="Already have an account? Sign in", border=0, 
                            fg='black', bg='white', cursor='hand2', 
                            font=('Microsoft YaHei UI Light', 9), command=self.go_to_login)
        login_link.place(x=90, y=530)

    def load_resources(self):
        """Tải ảnh an toàn"""
        img_dir = os.path.join(project_root, "images")
        
        def safe_load(filename, size=None):
            path = os.path.join(img_dir, filename)
            if not os.path.exists(path):
                # Fallback nếu không tìm thấy ảnh cụ thể
                if filename == "signup.png": 
                    path = os.path.join(img_dir, "login.png") # Thử dùng ảnh login thay thế
                    if not os.path.exists(path): return None
                else:
                    return None
            try:
                img = Image.open(path)
                if size: img = img.resize(size)
                return ImageTk.PhotoImage(img)
            except Exception: return None

        self.signup_img = safe_load("signup.png")
        self.eye_icon = safe_load("eye.png", (20, 20))
        self.eye_off_icon = safe_load("eye_off.png", (20, 20))

    def create_entry(self, frame, y, placeholder):
        """Helper tạo Entry thường với placeholder"""
        entry = Entry(frame, width=25, fg='black', border=0, bg='white', 
                      font=('Microsoft YaHei UI Light', 11))
        entry.place(x=30, y=y)
        entry.insert(0, placeholder)
        
        def on_enter(e):
            if entry.get() == placeholder:
                entry.delete(0, 'end')
        def on_leave(e):
            if not entry.get():
                entry.insert(0, placeholder)
                
        entry.bind('<FocusIn>', on_enter)
        entry.bind('<FocusOut>', on_leave)
        
        Frame(frame, width=295, height=2, bg='black').place(x=25, y=y+27)
        return entry

    def create_password_entry(self, frame, y, placeholder, toggle_type):
        """Helper tạo Password Entry"""
        entry = Entry(frame, width=25, fg='black', border=0, bg='white', 
                      font=('Microsoft YaHei UI Light', 11), show="")
        entry.place(x=30, y=y)
        entry.insert(0, placeholder)
        
        # Logic toggle visibility
        show_var = BooleanVar(value=False)
        
        # Nút mắt
        btn = Button(frame, image=self.eye_icon, bg='white', border=0, 
                     cursor='hand2')
        if self.eye_icon: # Chỉ hiện nếu load được icon
            btn.place(x=320, y=y)

        # Hàm toggle
        def toggle():
            if entry.get() == placeholder: return # Không toggle placeholder
            if show_var.get():
                entry.config(show="*")
                if self.eye_off_icon: btn.config(image=self.eye_off_icon)
                show_var.set(False)
            else:
                entry.config(show="")
                if self.eye_icon: btn.config(image=self.eye_icon)
                show_var.set(True)
        
        btn.config(command=toggle)

        # Logic placeholder
        def on_enter(e):
            if entry.get() == placeholder:
                entry.delete(0, 'end')
                if not show_var.get(): # Nếu đang mode ẩn
                    entry.config(show="*")
                    if self.eye_off_icon: btn.config(image=self.eye_off_icon)

        def on_leave(e):
            if not entry.get():
                entry.config(show="")
                entry.insert(0, placeholder)
                if self.eye_icon: btn.config(image=self.eye_icon)
                show_var.set(False)

        entry.bind('<FocusIn>', on_enter)
        entry.bind('<FocusOut>', on_leave)
        
        Frame(frame, width=295, height=2, bg='black').place(x=25, y=y+27)
        return entry

    def sanitize_input(self, text):
        if not isinstance(text, str): return ""
        return re.sub(r'[^\w\s\-@.]', '', text)[:100]

    def signup(self):
        username = self.sanitize_input(self.username.get())
        full_name = self.sanitize_input(self.name.get())
        email = self.sanitize_input(self.email.get())
        phone = self.sanitize_input(self.phone.get())
        # Lưu ý: Class User hiện tại chưa hỗ trợ lưu gender/dob, 
        # nhưng ta vẫn lấy dữ liệu để validate hoặc mở rộng sau này.
        gender = self.gender.get() 
        dob = self.dob.get()
        
        password = self.code.get() 
        confirm_password = self.confirm_code.get() 
        terms_accepted = self.terms.get()

        # Check Placeholders
        if (username == "Username" or full_name == "Full Name" or 
            email == "Email" or phone == "Phone Number" or 
            password == "Password" or confirm_password == "Confirm Password"):
            messagebox.showerror("Error", "All fields are required", parent=self.root)
            return

        if not username or not full_name or not email or not phone:
             messagebox.showerror("Error", "All fields are required", parent=self.root)
             return

        # Validate username
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            messagebox.showerror("Error", "Username must be 3-20 characters (letters, numbers, _)", parent=self.root)
            return

        # Validate email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format", parent=self.root)
            return

        # Validate phone (Update regex cho phép linh hoạt hơn)
        if not re.match(r"^[\d\+\-\s\(\)]{10,20}$", phone):
            messagebox.showerror("Error", "Invalid phone number", parent=self.root)
            return

        # Validate password
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters", parent=self.root)
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match", parent=self.root)
            return

        if not terms_accepted:
            messagebox.showerror("Error", "You must agree to the Terms of Service", parent=self.root)
            return

        user_data = {
            "username": username,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": password 
        }

        if not self.auth_manager:
            messagebox.showerror("Error", "System Error: AuthManager not available.")
            return

        result = self.auth_manager.register_user(user_data)
        
        if "Registered" in result or "successful" in result:
            messagebox.showinfo("Success", "Sign up successful! Please log in.", parent=self.root)
            self.go_to_login()
        else:
            messagebox.showerror("Error", result, parent=self.root)

    def go_to_login(self):
        self.root.destroy()
        try:
            from ui.login_ui import Login
            root = Tk()
            Login(root)
            root.mainloop()
        except ImportError:
             messagebox.showerror("Error", "Cannot find Login module.")