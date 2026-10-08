import json
import os
import uuid
from datetime import datetime
from filelock import FileLock

class NotificationManager:
    def __init__(self, file_path="data/notifications.json"):
        self.file_path = file_path
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {"notifications": []}

    def _save(self):
        try:
            with FileLock(f"{self.file_path}.lock"):
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {self.file_path}: {e}")
            raise Exception(f"Failed to save notifications: {e}")
    def add_notification(self, user_id, message):
        noti = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "message": message,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "read": False
        }
        self.data["notifications"].append(noti)
        self._save()

    # Trong notification_manager.py:
    def receive_notification(self, message, user_id=None):
        if user_id:
            self.add_notification(user_id, message)
        else:
            # Import cục bộ để tránh circular import
            try:
                from controllers.auth_manager import AuthManager
                for user in AuthManager().get_all_users():
                    self.add_notification(user["username"], message)
            except ImportError:
                pass # Bỏ qua nếu không load được AuthManager

    def get_notifications(self, user_id):
        return [n for n in self.data["notifications"] if n["user_id"] == user_id]

    def mark_all_as_read(self, user_id):
        for n in self.data["notifications"]:
            if n["user_id"] == user_id:
                n["read"] = True
        self._save()

    def delete_notification(self, notification_id):
        self.data["notifications"] = [n for n in self.data["notifications"] if n["id"] != notification_id]
        self._save()