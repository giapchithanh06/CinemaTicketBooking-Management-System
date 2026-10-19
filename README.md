# 🎬 TheaterManageApp - Cinema Ticket Booking & Management System

## 📌 Description

**TheaterManageApp** (Duo Cinema) is a desktop application for booking movie tickets and managing a cinema. It gives moviegoers a simple way to browse movies, pick a showtime, choose seats and receive an e-ticket with a QR code, while giving administrators a full dashboard to manage movies, showtimes, screening rooms, seats, tickets, users and revenue.

The application was built with **Python and Tkinter**, following a layered **Model – Controller – Service – UI** structure. Movie information and posters are fetched automatically from **The Movie Database (TMDB) API**, and all data is stored in local **JSON files**.

The project is packaged into a **Windows executable (.exe)** with PyInstaller, so it can be installed and launched from the Desktop like a normal application — **no Python installation required**.

## 💻 Download & Install (Windows App)

You can use TheaterManageApp as a regular Windows app without installing Python.

**1. Download**

Go to the [Releases](https://github.com/giapchithanh06/TheManagerApp/releases) page and download `TheaterManageApp.zip`.

**2. Extract**

Extract the zip file to any folder, for example:

```
C:\Program Files\TheaterManageApp\
```

The folder contains:

```
TheaterManageApp/
├── TheaterManageApp.exe     # Application launcher
└── _internal/               # Libraries, data and images (do not delete)
```

> ⚠️ Keep `TheaterManageApp.exe` and the `_internal` folder together. The app will not start if they are separated.

**3. Create a Desktop Shortcut**

- Right-click `TheaterManageApp.exe`
- Choose **Show more options → Send to → Desktop (create shortcut)**
- Launch the app by double-clicking the **TheaterManageApp** icon on your Desktop

**Optional:**
- Right-click the shortcut → **Pin to Start** or **Pin to taskbar** for quick access
- Rename the shortcut to **Duo Cinema** if you like

**4. First Launch**

Windows SmartScreen may show *"Windows protected your PC"* because the app is not digitally signed.
Click **More info → Run anyway** to continue.

## 🚀 Features

### 👤 Customer Features

**Authentication**
- Splash screen when the app starts
- User Registration with validation (username, email, phone number, password)
- User Login
- Show / hide password
- Forgot Password (verified by email and phone number)
- Passwords encrypted with bcrypt

**Movie Browsing**
- Now-showing movies
- Upcoming movies
- Movie posters, genres, runtime and age rating
- Movie data updated automatically from TMDB API

**Ticket Booking (4 steps)**
1. Select movie, date and showtime
2. Select seats on an interactive seat map
3. Confirm customer information (name, email, phone)
4. Receive an e-ticket with QR code

**Seat Map**
- Standard seats – 80,000 VND
- VIP seats (rows F–J) – 100,000 VND
- Sweetbox seats (row K) – 120,000 VND
- Booked and selected seats shown in different colors
- Automatic price calculation

**My Account**
- View purchased tickets
- Show the QR code of each ticket
- News & events
- Personal notifications with "mark as read"

### 👨‍💼 Admin Features

**Dashboard**
- Overview statistic cards
- Quick actions (add movie, manage showtimes, check tickets)
- Top revenue movies
- Recent transactions

**Revenue Statistics**
- Revenue by month and year
- Daily revenue and ticket count
- Top movies of the month

**Movie Management**
- Movie list with search and status filter
- Add new movies (now showing / upcoming)

**Cinema Management**
- Cinema information
- Showtime management (list, add) with automatic schedule generation
- Screening room management (list, add)
- Seat management: view the seat map of each room, enable/disable seats, normalize seat types

**Ticket Management**
- Search booked tickets
- Cancel tickets

**User Management**
- Search users by username or email
- Double-click a user to view their ticket purchase history

**News Management**
- News list
- Publish news

**System**
- Admin profile update
- Activity log (audit log) of important actions

## 🛠️ Technologies Used

- Python 3.13
- Tkinter / ttk
- Pillow (PIL)
- Requests
- TMDB API
- bcrypt
- filelock
- qrcode
- JSON
- PyInstaller

## ✨ Techniques Applied

### 🏗️ Layered Architecture
The source code is split into separate layers:
- **models** – data objects (Movie, Ticket, User) with validation
- **controllers** – business logic (authentication, movies, showtimes, rooms, seats, tickets, news, notifications, QR codes)
- **services** – external API and booking flow
- **ui** – Tkinter screens for login, sign-up, customer and admin

### 🔔 Observer Pattern
Managers notify the interface when data changes (new movie, new showtime, seat update…), so screens and notifications are refreshed automatically.

### 🌐 TMDB API Integration
- Fetches now-showing and upcoming movies in Vietnamese (`vi-VN`, region `VN`)
- Gets genres, runtime, director, cast and age rating
- Downloads and caches posters locally
- Runs in a background thread so the interface does not freeze
- Retries failed requests automatically

### 🔒 Security & Data Safety
- Passwords hashed with **bcrypt**
- **FileLock** prevents data corruption when JSON files are written
- User input is sanitized and validated

### 🎟️ QR Code E-ticket
Each ticket generates a QR code that can be shown at the cinema.

### 🖥️ High-DPI Support
The app detects the screen scaling (125%, 150%…) and resizes windows accordingly, so the interface stays sharp on modern displays.

### 📦 Executable Packaging
- Packaged with PyInstaller into a standalone Windows app
- The app automatically finds its `data` and `images` folders when running from the `.exe`

## 📂 Project Structure

```
TheaterManageApp/
│
├── TheaterManageApp/
│   ├── TheaterManageApp.py        # Main entry point (splash screen + login)
│   ├── main.py                    # Alternative entry point (login only)
│   │
│   ├── models/
│   │   ├── movie.py
│   │   ├── ticket.py
│   │   └── user.py
│   │
│   ├── controllers/
│   │   ├── auth_manager.py
│   │   ├── movie_manager.py
│   │   ├── showtime_manager.py
│   │   ├── theater_manager.py
│   │   ├── seat_manager.py
│   │   ├── ticket_manager.py
│   │   ├── news_manager.py
│   │   ├── notification_manager.py
│   │   └── qr_generator.py
│   │
│   ├── services/
│   │   ├── api_crawler.py         # TMDB API client
│   │   └── place_ticket.py        # 4-step booking flow
│   │
│   ├── ui/
│   │   ├── login_ui.py
│   │   ├── sign_up.py
│   │   ├── user_ui.py
│   │   ├── admin_ui.py
│   │   └── support.py
│   │
│   ├── data/                      # JSON database
│   │   ├── users.json
│   │   ├── movies.json
│   │   ├── showtimes.json
│   │   ├── theaters.json
│   │   ├── seats.json
│   │   ├── tickets.json
│   │   ├── notifications.json
│   │   ├── audit_logs.json
│   │   ├── cinema.json
│   │   └── cache.json
│   │
│   └── images/
│       ├── posters/               # Movie posters downloaded from TMDB
│       ├── qrcodes/               # Generated ticket QR codes
│       └── UI Resources           # Logo, icons, backgrounds
│
└── dist/
    └── TheaterManageApp/          # Built Windows application
        ├── TheaterManageApp.exe
        └── _internal/
```

## 🎨 User Interface

- Splash screen with auto-redirect
- Clean login and sign-up screens
- Customer interface with tab navigation: Quick Booking, Now Showing, Upcoming, News, Notifications
- Movie cards with posters
- Step-by-step booking with progress indicator
- Color-coded interactive seat map
- Admin dashboard with sidebar menu and collapsible sub-menus
- Tables (Treeview) for lists and statistics

## ⚙️ System Architecture

```
UI (Tkinter)
   ↓
Services (Booking flow, TMDB API)
   ↓
Controllers (Business logic)
   ↓
Models
   ↓
JSON Data Files
```

Benefits:
- Maintainability
- Scalability
- Code Reusability
- Better Project Organization

## ▶️ How to Run

### Option 1: Run the Windows App (Recommended)

See **💻 Download & Install** above — just download, extract and double-click `TheaterManageApp.exe`.

### Option 2: Run from Source Code

**1. Clone the Repository**

```bash
git clone https://github.com/giapchithanh06/TheManagerApp.git
cd TheManagerApp/TheaterManageApp
```

**2. Install Python Libraries**

Requires **Python 3.10+**.

```bash
pip install pillow requests bcrypt filelock qrcode
```

**3. Run the Application**

```bash
python TheaterManageApp.py
```

Recommended Tools:
- Visual Studio Code
- PyCharm

### Option 3: Build the .exe Yourself

```bash
pip install pyinstaller
cd TheaterManageApp
pyinstaller --noconfirm --onedir --windowed ^
  --name TheaterManageApp ^
  --icon images/cinema.ico ^
  --add-data "data;data" ^
  --add-data "images;images" ^
  TheaterManageApp.py
```

The app will be created in `dist/TheaterManageApp/`.

## 🔑 Accounts

- Customers can create a new account on the **Sign Up** screen.
- Administrator accounts are users with `"type": "Admin"` in `data/users.json`. Logging in with an admin account opens the Admin Dashboard automatically.

## 🎯 Purpose

This project was developed for educational purposes to practice:
- Python Programming
- Object-Oriented Programming (OOP)
- Desktop GUI Development with Tkinter
- Software Architecture & Design Patterns
- REST API Integration
- Data Management with JSON
- Password Security
- Application Packaging & Distribution
- Team Collaboration with Git & GitHub

## 🚀 Future Improvements

- Database Integration (SQLite / MySQL)
- Online Payment Gateway Integration
- Email delivery of e-tickets
- QR code scanning at the cinema entrance
- Seat locking in real time for multiple users
- Food & drink combos
- Movie reviews and ratings
- Revenue charts
- Installer (.msi / setup.exe) with automatic Desktop shortcut
- Web and mobile versions

## 👨‍💻 Authors

**giapchithanh06**

Student Project – Cinema Ticket Booking & Management System

## 📄 License

This project is intended for educational and learning purposes only.

Movie data and posters are provided by [The Movie Database (TMDB)](https://www.themoviedb.org/). This product uses the TMDB API but is not endorsed or certified by TMDB.
