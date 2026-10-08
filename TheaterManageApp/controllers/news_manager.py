import json
import os
import uuid
import re
from datetime import datetime
from filelock import FileLock
from models.movie import validate_date
from controllers.notification_manager import NotificationManager  # Import NotificationManager for notifications
from controllers.auth_manager import AuthManager  # Import AuthManager for admin validation

class News:
    def __init__(self, news_id, title, content, admin_username, created_at=None):
        self.news_id = str(news_id) if news_id else str(uuid.uuid4())
        self.title = title or "No Title"
        self.content = content or "No Content"
        self.admin_username = admin_username or "Unknown"
        self.created_at = created_at or datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    def to_dict(self):
        return {
            "news_id": self.news_id,
            "title": self.title,
            "content": self.content,
            "admin_username": self.admin_username,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data):
        return News(
            news_id=data.get("news_id"),
            title=data.get("title", "No Title"),
            content=data.get("content", "No Content"),
            admin_username=data.get("admin_username", "Unknown"),
            created_at=data.get("created_at", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
        )

    def validate(self):
        if not self.news_id:
            raise ValueError("news_id is required")
        if not self.title or self.title == "No Title":
            raise ValueError("title is required")
        if not self.content or self.content == "No Content":
            raise ValueError("content is required")
        if not self.admin_username or self.admin_username == "Unknown":
            raise ValueError("admin_username is required")
        if not re.match(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}", self.created_at):
            raise ValueError("created_at must be in DD-MM-YYYY HH:MM:SS format")

class NewsManager:
    def __init__(self, file_path="data/news.json", auth_manager=None):
        self.file_path = file_path
        self.auth_manager = auth_manager or AuthManager()
        self.notification_manager = NotificationManager()  # Initialize NotificationManager
        self.news = self.load_news()
        self._observers = []  # For Observer Logic

    def register_observer(self, callback):
        """Register a callback for notifications (Observer Logic)."""
        self._observers.append(callback)

    def notify_observers(self, message):
        """Notify all observers of a change (e.g., for news_ui.py)."""
        for callback in self._observers:
            callback(message)

    def load_news(self):
        """Load news from JSON file with proper error handling."""
        if os.path.exists(self.file_path):
            try:
                with FileLock(f"{self.file_path}.lock"):
                    with open(self.file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        return [News.from_dict(item) for item in data.get("news", [])]
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {self.file_path}: {e}")
            except ValueError as e:
                print(f"Validation error in {self.file_path}: {e}")
            except OSError as e:
                print(f"Error reading {self.file_path}: {e}")
        return []

    def save_news(self):
        """Save news to JSON file with file locking."""
        try:
            with FileLock(f"{self.file_path}.lock"):
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, 'w', encoding='utf-8') as file:
                    json.dump({"news": [item.to_dict() for item in self.news]}, file, ensure_ascii=False, indent=4)
        except OSError as e:
            print(f"Error writing to {self.file_path}: {e}")
            raise Exception(f"Failed to save news: {e}")
    def validate_admin(self, admin_username):
        """Check if admin_username is an admin using AuthManager."""
        user = self.auth_manager.get_user_by_username(admin_username)
        return user is not None and user.type == "Admin"

    def sanitize_input(self, text):
        """Sanitize input to prevent injection attacks."""
        if not isinstance(text, str):
            return ""
        # Remove HTML tags, script tags, and limit length
        text = re.sub(r'<[^>]+>|[<>]', '', text)
        return text.strip()[:500]  # Limit to 500 characters

    def add_news(self, title, content, admin_username, current_user=None, automated=False):
        if not automated:
            if not current_user or current_user.get("type") != "Admin":
                return "Only admins can add news!"
            if current_user.get("username") != admin_username:
                return "Admin username does not match current user!"

        if not self.validate_admin(admin_username):
            return f"Admin '{admin_username}' does not exist or is not an admin!"

        news_item = News(
            news_id=None,
            title=self.sanitize_input(title),
            content=self.sanitize_input(content),
            admin_username=admin_username
        )
        try:
            news_item.validate()
        except ValueError as e:
            return f"Error adding news: {e}"

        if any(n.news_id == news_item.news_id for n in self.news):
            return f"News item with ID '{news_item.news_id}' already exists!"

        self.news.append(news_item)
        self.save_news()
        self.notify_observers(f"New news item '{news_item.title}' added by '{admin_username}'.")
        if not automated:
            self.notification_manager.receive_notification(
                f"Tin tức mới: {news_item.title} - {news_item.content}",
                user_id=None  # Notify all users
            )
        return f"Added news: '{news_item.title}'!"

    def update_news(self, news_id, title, content, admin_username, current_user=None):
        if not current_user or current_user.get("type") != "Admin":
            return "Only admins can update news!"
        if current_user.get("username") != admin_username:
            return "Admin username does not match current user!"

        if not self.validate_admin(admin_username):
            return f"Admin '{admin_username}' does not exist or is not an admin!"

        for news_item in self.news:
            if news_item.news_id == news_id:
                news_item.title = self.sanitize_input(title)
                news_item.content = self.sanitize_input(content)
                news_item.admin_username = admin_username
                try:
                    news_item.validate()
                except ValueError as e:
                    return f"Error updating news: {e}"
                self.save_news()
                self.notify_observers(f"News item '{news_item.title}' (ID: {news_id}) updated by '{admin_username}'.")
                self.notification_manager.receive_notification(
                    f"Tin tức đã cập nhật: {news_item.title} - {news_item.content}",
                    user_id=None  # Notify all users
                )
                return f"Updated news: '{news_item.title}'!"
        return f"News item with ID '{news_id}' not found!"

    def delete_news(self, news_id, current_user=None):
        if not current_user or current_user.get("type") != "Admin":
            return "Only admins can delete news!"

        news_item = next((n for n in self.news if n.news_id == news_id), None)
        if not news_item:
            return f"News item with ID '{news_id}' not found!"

        self.news = [n for n in self.news if n.news_id != news_id]
        self.save_news()
        self.notify_observers(f"News item '{news_item.title}' (ID: {news_id}) deleted by '{current_user.get('username')}'.")
        self.notification_manager.receive_notification(
            f"Tin tức '{news_item.title}' đã bị xóa.",
            user_id=None  # Notify all users
        )
        return f"Deleted news: '{news_item.title}'!"

    def get_all_news(self):
        return [n.to_dict() for n in self.news]

    def receive_notification(self, message, admin_username="System"):
        return self.add_news(
            title="System Notification",
            content=message,
            admin_username=admin_username,
            automated=True
        )

    def receive_notification(self, message, admin_username="System"):
        """Receive automated notifications from other managers."""
        return self.add_news(
            title="System Notification",
            content=message,
            admin_username=admin_username,
            automated=True
        )