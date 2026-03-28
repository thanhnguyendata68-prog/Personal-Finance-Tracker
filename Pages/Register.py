import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import os
import subprocess
import sys

DB_NAME = "users.db"

def connect_db():
  return sqlite3.connect(DB_NAME)

def create_users_table():
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      salt TEXT NOT NULL
    )
  ''')
  conn.commit()
  conn.close()

def hash_password(password, salt=None):
  if salt is None:
    salt = os.urandom(16)
  password_bytes = password.encode('utf-8')
  hashed = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, 100000)
  return hashed.hex(), salt.hex()

def username_exists(username):
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
  result = cursor.fetchone()
  conn.close()
  return result is not None

def create_account():
  username = username_entry.get().strip()
  password = password_entry.get().strip()
  confirm_password = confirm_password_entry.get().strip()

  error_label.config(text="")

  if not username:
    error_label.config(text="Username cannot be empty.")
    return

  if not password:
    error_label.config(text="Password should not be empty.")
    return
  
  if password != confirm_password:
    error_label.config(text="Passwords do not match.")
    return
  
  if username_exists(username):
    error_label.config(text="Username already exists. Please choose another.")
    return

  password_hash, salt = hash_password(password)

  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", (username, password_hash, salt))
  conn.commit()
  conn.close()

  messagebox.showinfo("Account Created", "Your account has been created successfully!")
  root.destroy()
  subprocess.Popen([sys.executable, "Pages/Login.py"])

def back_to_login():
  root.destroy()
  subprocess.Popen([sys.executable, "Pages/Login.py"])

create_users_table()

root = tk.Tk()
root.title("Register Page")
root.geometry("400x380")
root.resizable(False, False)

title_label = tk.Label(root, text="Register", font=("Arial", 18, "bold"))
title_label.pack(pady=15)

username_label = tk.Label(root, text="Username")
username_label.pack()
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

password_label = tk.Label(root, text="Password")
password_label.pack()
password_entry = tk.Entry(root, width=30, show="*")
password_entry.pack(pady=5)

confirm_password_label = tk.Label(root, text="Confirm Password")
confirm_password_label.pack()
confirm_password_entry = tk.Entry(root, width=30, show="*")
confirm_password_entry.pack(pady=5)

create_account_button = tk.Button(root, text="Create Account", width=20, command=create_account)
create_account_button.pack(pady=10)

back_button = tk.Button(root, text="Back to Login", width=20, command=back_to_login)
back_button.pack(pady=5)

error_label = tk.Label(root, text="", fg="red", font=("Arial", 10))
error_label.pack(pady=10)

root.mainloop()