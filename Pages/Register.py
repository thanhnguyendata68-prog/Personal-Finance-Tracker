"""
Pages/Register.py — Account registration screen for Personal Finance Tracker.
"""

import tkinter as tk
import os
import sys
import subprocess

# ── Resolve paths & import shared module ──────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from db import THEME as T, FONT as FF, connect_db, create_all_tables, hash_password
from ui_helpers import make_entry, center_window


# ── Helpers ────────────────────────────────────────────────────────────────────
def _username_exists(username: str) -> bool:
    conn = connect_db()
    c    = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None


def _password_strength(pw: str) -> tuple:
    """
    Returns (label, color) describing password strength.
    Criteria: length, digits, uppercase, special chars.
    """
    score = 0
    if len(pw) >= 8:  score += 1
    if any(c.isdigit() for c in pw):   score += 1
    if any(c.isupper() for c in pw):   score += 1
    if any(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/" for c in pw): score += 1

    if score <= 1: return "Weak",   T["red"]
    if score == 2: return "Fair",   T["yellow"]
    if score == 3: return "Good",   T["accent"]
    return "Strong", T["green"]


# ── Registration Logic ─────────────────────────────────────────────────────────
def create_account():
    username         = username_var.get().strip()
    password         = password_var.get().strip()
    confirm_password = confirm_var.get().strip()
    error_var.set("")

    if not username:
        error_var.set("⚠  Username cannot be empty.")
        return

    if len(password) < 6:
        error_var.set("⚠  Password must be at least 6 characters.")
        return

    if password != confirm_password:
        error_var.set("✗  Passwords do not match.")
        return

    if _username_exists(username):
        error_var.set("✗  Username already taken. Please choose another.")
        return

    password_hash, salt = hash_password(password)

    conn = connect_db()
    c    = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
        (username, password_hash, salt)
    )
    conn.commit()
    conn.close()

    root.destroy()
    # Redirect to Login after successful registration
    subprocess.Popen([
        sys.executable,
        os.path.join(os.path.dirname(__file__), "Login.py")
    ])


def back_to_login():
    root.destroy()
    subprocess.Popen([
        sys.executable,
        os.path.join(os.path.dirname(__file__), "Login.py")
    ])


# ── UI ─────────────────────────────────────────────────────────────────────────
create_all_tables()

root = tk.Tk()
root.title("Personal Finance Tracker — Register")
root.resizable(False, False)
root.configure(bg=T["bg"])
center_window(root, 440, 600)

# ── Logo / Title ───────────────────────────────────────────────────────────────
top = tk.Frame(root, bg=T["bg"])
top.pack(pady=(36, 8))

tk.Label(top, text="💰", font=(FF, 34), bg=T["bg"], fg=T["accent"]).pack()
tk.Label(top, text="Create Your Account",
         font=(FF, 16, "bold"), bg=T["bg"], fg=T["text"]).pack(pady=(4, 0))
tk.Label(top, text="Start tracking your finances today",
         font=(FF, 10), bg=T["bg"], fg=T["subtext"]).pack()

# ── Card ───────────────────────────────────────────────────────────────────────
card = tk.Frame(root, bg=T["card"], padx=36, pady=24)
card.pack(padx=40, pady=14, fill="x")

username_var = tk.StringVar()
password_var = tk.StringVar()
confirm_var  = tk.StringVar()
error_var    = tk.StringVar()

# Username
tk.Label(card, text="Username", font=(FF, 10),
         bg=T["card"], fg=T["subtext"]).pack(anchor="w", pady=(0, 2))
make_entry(card, username_var)

# Password + strength indicator
tk.Label(card, text="Password", font=(FF, 10),
         bg=T["card"], fg=T["subtext"]).pack(anchor="w", pady=(10, 2))

strength_var   = tk.StringVar()
strength_color = tk.StringVar(value=T["subtext"])

def _on_password_change(*_):
    pw = password_var.get()
    if pw:
        label, color = _password_strength(pw)
        strength_var.set(f"Strength: {label}")
        strength_lbl.config(fg=color)
    else:
        strength_var.set("")

password_var.trace_add("write", _on_password_change)
make_entry(card, password_var, show="•")

strength_lbl = tk.Label(card, textvariable=strength_var, font=(FF, 9),
                         bg=T["card"], fg=T["subtext"])
strength_lbl.pack(anchor="w", pady=(2, 0))

# Confirm password
tk.Label(card, text="Confirm Password", font=(FF, 10),
         bg=T["card"], fg=T["subtext"]).pack(anchor="w", pady=(10, 2))
make_entry(card, confirm_var, show="•")

# Error message
tk.Label(card, textvariable=error_var, font=(FF, 9),
         bg=T["card"], fg=T["red"], wraplength=320).pack(pady=(10, 0))

# ── Create Account Button ──────────────────────────────────────────────────────
create_btn = tk.Button(
    card, text="Create Account", font=(FF, 11, "bold"),
    bg=T["accent"], fg="white",
    activebackground=T["accent_hover"], activeforeground="white",
    relief="flat", cursor="hand2", command=create_account
)
create_btn.pack(fill="x", ipady=10, pady=(14, 0))
create_btn.bind("<Enter>", lambda _: create_btn.config(bg=T["accent_hover"]))
create_btn.bind("<Leave>", lambda _: create_btn.config(bg=T["accent"]))

# ── Back to Login Link ─────────────────────────────────────────────────────────
bottom = tk.Frame(root, bg=T["bg"])
bottom.pack(pady=8)

tk.Label(bottom, text="Already have an account?", font=(FF, 9),
         bg=T["bg"], fg=T["subtext"]).pack(side="left")

login_link = tk.Label(bottom, text=" Sign in", font=(FF, 9, "underline"),
                      bg=T["bg"], fg=T["accent"], cursor="hand2")
login_link.pack(side="left")
login_link.bind("<Button-1>", lambda _: back_to_login())

# ── Key bindings ───────────────────────────────────────────────────────────────
root.bind("<Return>", lambda _: create_account())

root.mainloop()