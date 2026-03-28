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
  cursor.execute("""
      CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          salt TEXT NOT NULL
      )
    """)
  conn.commit()
  conn.close()

def hash_password(password, salt=None):
  if salt is None:
    salt = os.urandom(16)
  password_bytes = password.encode('utf-8')
  hashed = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, 100000)
  return hashed.hex(), salt.hex()

def verify_password(stored_hash, stored_salt, entered_password):
  salt_bytes = bytes.fromhex(stored_salt)
  entered_hash, _ = hash_password(entered_password, salt_bytes)
  return entered_hash == stored_hash

def login():
  username = username_entry.get().strip()
  password = password_entry.get().strip()

  error_label.config(text="")

  if not username or not password:
    error_label.config(text="Please enter both username and password." )
    return
  
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
  user = cursor.fetchone()
  conn.close()

  if user:
    stored_hash, stored_salt = user
    if verify_password(stored_hash, stored_salt, password):
      messagebox.showinfo("Login Successful", f"Welcome, {username}!")
      root.destroy()
      subprocess.Popen([sys.executable, "Dashboard.py"])
    else:
      error_label.config(text="Wrong username or password.")
  else:
    error_label.config(text="Wrong username or password.")

def open_registration():
  root.destroy()
  subprocess.Popen([sys.executable, "Pages/Register.py"])

create_users_table()

root = tk.Tk()
root.title("Login Page")
root.geometry("400x320")
root.resizable(False, False)

title_label = tk.Label(root, text="Login", font=("Arial", 18, "bold"))
title_label.pack(pady=15)

username_label = tk.Label(root, text="Username")
username_label.pack()
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

password_label = tk.Label(root, text="Password")
password_label.pack()
password_entry = tk.Entry(root, width=30, show="*")
password_entry.pack(pady=5)

login_button = tk.Button(root, text="Login", width=20, command=login)
login_button.pack(pady=10)

register_button = tk.Button(root, text="Register", width=20, command=open_registration)
register_button.pack(pady=5)

error_label = tk.Label(root, text="", fg="red", font=("Arial", 10))
error_label.pack(pady=10)

root.mainloop()