import json
import os
import qrcode
from PIL import Image

def generate_ticket_qr(ticket_info):
    """Tạo mã QR từ thông tin vé."""
    # Đảm bảo ticket_info có thể serialize JSON
    if not isinstance(ticket_info, dict):
        raise ValueError("ticket_info phải là dictionary")

    # Tạo đường dẫn tuyệt đối
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_path, "images", "qrcodes")
    os.makedirs(output_dir, exist_ok=True)
    
    file_name = f"qr_{ticket_info.get('ticket_id', 'unknown')}.png"
    file_path = os.path.join(output_dir, file_name)

    # Tạo dữ liệu QR string
    qr_str = "\n".join([f"{k}: {v}" for k, v in ticket_info.items()])

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_str)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_path)

    return file_path