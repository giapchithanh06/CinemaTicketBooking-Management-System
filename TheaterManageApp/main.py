
import tkinter as tk
from tkinter import messagebox
from ui.login_ui import Login
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)  # Luôn đọc data/ trong thư mục dự án dù chạy từ đâu
if project_root not in sys.path:
    sys.path.append(project_root)
from services.api_crawler import MovieCrawler 
def main():
    
        root = tk.Tk()
        
        root.title("Movie Ticket Booking System")
        root.configure(bg="#fff")
        
        app = Login(root)
        
        root.mainloop()

if __name__ == "__main__":
    main()