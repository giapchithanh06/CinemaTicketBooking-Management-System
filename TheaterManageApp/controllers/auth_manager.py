import json
import os
import uuid
import bcrypt
from filelock import FileLock
from controllers.notification_manager import NotificationManager

try: from models.user import User, Admin
except ImportError:
    class User: pass
    class Admin: pass

class AuthManager:
    def __init__(self, user_file_path="data/users.json"):
        self.user_file_path = user_file_path
        self.users = []
        self.current_user = None
        try: self.notification_manager = NotificationManager()
        except: self.notification_manager = None
        self.load_users()

    @staticmethod
    def _hash_password(pw):
        return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') if pw else ""

    @staticmethod
    def _check_password(pw, hashed):
        try: return bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))
        except: return False

    def load_users(self):
        self.users = []
        if os.path.exists(self.user_file_path):
            try:
                with FileLock(f"{self.user_file_path}.lock", timeout=5):
                    with open(self.user_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for d in data.get('users', []):
                            cls = Admin if d.get('type') == 'Admin' else User
                            if hasattr(cls, 'from_dict'): self.users.append(cls.from_dict(d))
            except: pass
        return self.users

    def save_users(self):
        try:
            with FileLock(f"{self.user_file_path}.lock", timeout=5):
                data = [u.to_dict() for u in self.users if hasattr(u, 'to_dict')]
                with open(self.user_file_path, 'w', encoding='utf-8') as f:
                    json.dump({"users": data}, f, indent=4, ensure_ascii=False)
        except: pass

    def register_user(self, data):
        if self.get_user_by_username(data.get("username")): return "Username already exists!"
        try:
            h = self._hash_password(data.get("password"))
            u = User(str(uuid.uuid4()), data["username"], h, data["full_name"], data["phone"], data["email"])
            self.users.append(u); self.save_users()
            return f"Registered User '{u.username}'!"
        except Exception as e: return f"Error: {e}"

    def update_user(self, uid, data, is_admin=False):
        u = next((x for x in self.users if str(x.user_id) == str(uid)), None)
        if u:
            if "full_name" in data: u.full_name = data["full_name"]
            if "email" in data: u.email = data["email"]
            if "phone" in data: u.phone = data["phone"]
            if is_admin: 
                for k in ["position", "birth_date", "gender", "address"]: 
                    if k in data and hasattr(u, k): setattr(u, k, data[k])
            self.save_users(); return "Updated successfully!"
        return "User not found"

    # --- HÀM MỚI: QUÊN MẬT KHẨU ---
    def reset_password(self, email, phone, new_password):
        """
        Tìm user có Email và Phone khớp, sau đó đổi pass.
        """
        self.load_users()
        target_user = None
        
        for u in self.users:
            if u.email == email and u.phone == phone:
                target_user = u
                break
        
        if not target_user:
            return False, "Không tìm thấy tài khoản khớp với Email và Số điện thoại này."

        # Đổi mật khẩu
        target_user.password = self._hash_password(new_password)
        self.save_users()
        return True, f"Đổi mật khẩu thành công cho tài khoản '{target_user.username}'!"

    def login(self, e, p):
        self.load_users()
        for u in self.users:
            if u.email == e and self._check_password(p, u.password):
                if hasattr(u, 'login'): u.login()
                self.current_user = u; self.save_users(); return f"Login successful for '{u.username}'!"
        return "Incorrect email or password"

    def logout(self, u):
        usr = self.get_user_by_username(u)
        if usr: 
            if hasattr(usr, 'logout'): usr.logout()
            self.current_user = None; self.save_users()

    def get_user_by_username(self, uname): return next((u for u in self.users if u.username == uname), None)
    def get_current_user(self): return self.current_user.to_dict() if self.current_user else None
    def get_all_users(self): return [u.to_dict() for u in self.users]