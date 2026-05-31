# 💰 Personal Finance Tracker

> A Python desktop application for managing personal income, expenses, budgets, and savings — built with Tkinter, SQLite, and Matplotlib.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.x-orange?logo=matplotlib&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **Secure Authentication** | PBKDF2-SHA256 password hashing with unique per-user salt |
| 👥 **Multi-User Support** | Each account sees only their own data |
| 📊 **Dashboard** | Live stat cards (balance, income, expenses, savings) with a donut chart |
| 💸 **Transaction Management** | Add, view, and delete income/expense records with categories |
| 💰 **Budget Manager** | Set custom monthly budgets with a colour-coded progress bar |
| 📈 **Financial Reports** | 6-month income vs expense bar chart + category pie breakdown |
| 🗄 **SQLite Persistence** | Lightweight local database — no server required |
| 🎨 **Modern Dark UI** | Polished dark theme with focus animations and hover effects |

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.8+** | Core application language |
| **Tkinter** | Cross-platform desktop GUI |
| **SQLite 3** | Local relational data storage |
| **Matplotlib** | Embedded charts (bar, pie, donut) |
| **hashlib (PBKDF2)** | Cryptographic password hashing |

---

## 📁 Project Structure

```
Personal Finance Tracker/
├── db.py              # Shared module: DB schema, auth, theme, queries
├── Dashboard.py       # Main dashboard window (entry point after login)
├── Transaction.py     # Add & manage income/expense transactions
├── users.db           # SQLite database (auto-created on first run)
└── Pages/
    ├── Login.py       # User login screen
    ├── Register.py    # New account registration
    └── Reports.py     # Financial reports & chart visualisations
```

---

## 🚀 Getting Started

### 1. Install dependency

```bash
pip install matplotlib
```

### 2. Run the application

```bash
python Pages/Login.py
```

Register a new account, then log in — you'll land on the Dashboard.

---

## 🔑 Security Notes

- Passwords are **never stored in plain text**
- Each password is hashed with **PBKDF2-HMAC-SHA256** and 100,000 iterations
- A **unique random salt** is generated per user, stored alongside the hash
- SQL queries use **parameterised statements** throughout (no injection risk)

---

## 🧠 What I Learned

- Designing **modular Python applications** with a shared utility layer (`db.py`)
- Implementing **industry-standard password security** (PBKDF2 + salt)
- Embedding **Matplotlib charts** inside Tkinter windows (`FigureCanvasTkAgg`)
- Managing **SQLite schema migrations** (`ALTER TABLE`) without data loss
- Building a **multi-window Tkinter app** using subprocess for process isolation
- Applying a consistent **design system** (colours, fonts, spacing) across all screens