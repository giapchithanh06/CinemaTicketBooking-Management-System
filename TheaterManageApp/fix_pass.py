import json
import bcrypt # Đảm bảo đã cài: pip install bcrypt

# File dữ liệu của bạn
file_path = "data/users.json"

# Mật khẩu bạn muốn đặt
new_password = "123456"
target_email = "minhluan2011@gmail.com"

try:
    # 1. Đọc file JSON hiện tại
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. Tìm user và cập nhật mật khẩu mới
    for user in data['users']:
        if user['email'] == target_email:
            # Tạo hash thực sự trên máy tính của bạn
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user['password'] = hashed.decode('utf-8')
            print(f"✅ Đã cập nhật mật khẩu cho {target_email}")
            break

    # 3. Lưu lại file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("🎉 Xong! Hãy chạy lại phần mềm và đăng nhập bằng mật khẩu 123456")

except Exception as e:
    print(f"❌ Lỗi: {e}")
