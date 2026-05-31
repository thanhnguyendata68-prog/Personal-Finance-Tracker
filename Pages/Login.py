"""
Pages/Login.py — Login screen for Personal Finance Tracker.
"""

import tkinter as tk
import os
import sys
import subprocess

# ── Resolve paths & import shared module ──────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from db import THEME as T, FONT as FF, connect_db, create_all_tables, verify_password


# ── Helpers ────────────────────────────────────────────────────────────────────
def _center_window(win, w, h):
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


def _make_entry(parent, var, show=None):
    """Styled dark-theme Entry with focus highlight border."""
    border = tk.Frame(parent, bg=T["border"], padx=1, pady=1)
    entry = tk.Entry(
        border, textvariable=var, show=show,
        bg=T["input_bg"], fg=T["text"],
        insertbackground=T["accent"],
        relief="flat", font=(FF, 11), bd=0
    )
    entry.pack(fill="x", ipady=9, padx=8)
    border.pack(fill="x", pady=(0, 2))

    def _focus_in(_):  border.config(bg=T["accent"])
    def _focus_out(_): border.config(bg=T["border"])
    entry.bind("<FocusIn>",  _focus_in)
    entry.bind("<FocusOut>", _focus_out)
    return entry


# ── Login Logic ────────────────────────────────────────────────────────────────
def login():
    username = username_var.get().strip()
    password = password_var.get().strip()
    error_var.set("")

    if not username or not password:
        error_var.set("⚠  Please enter both username and password.")
        return

    conn = connect_db()
    c    = conn.cursor()
    c.execute(
        "SELECT id, password_hash, salt FROM users WHERE username = ?",
        (username,)
    )
    user = c.fetchone()
    conn.close()

    if user:
        user_id, stored_hash, stored_salt = user
        if verify_password(stored_hash, stored_salt, password):
            root.destroy()
            # ✔ Fixed: redirect to Dashboard, not Transaction
            script = os.path.join(ROOT_DIR, "Dashboard.py")
            subprocess.Popen([sys.executable, script, str(user_id)])
            return

    error_var.set("✗  Invalid username or password.")


def open_register():
    root.destroy()
    subprocess.Popen([
        sys.executable,
        os.path.join(os.path.dirname(__file__), "Register.py")
    ])


# ── UI ─────────────────────────────────────────────────────────────────────────
create_all_tables()

root = tk.Tk()
root.title("Personal Finance Tracker — Login")
root.resizable(False, False)
root.configure(bg=T["bg"])
_center_window(root, 440, 530)

# ── Logo / Title ───────────────────────────────────────────────────────────────
top = tk.Frame(root, bg=T["bg"])
top.pack(pady=(44, 8))

tk.Label(top, text="💰", font=(FF, 38), bg=T["bg"], fg=T["accent"]).pack()
tk.Label(top, text="Personal Finance Tracker",
         font=(FF, 16, "bold"), bg=T["bg"], fg=T["text"]).pack(pady=(4, 0))
tk.Label(top, text="Sign in to your account",
         font=(FF, 10), bg=T["bg"], fg=T["subtext"]).pack()

# ── Info hint for new users ───────────────────────────────────────────────────
hint = tk.Frame(root, bg="#2a2d1e", padx=14, pady=10)
hint.pack(padx=40, fill="x")

hint_row = tk.Frame(hint, bg="#2a2d1e")
hint_row.pack(anchor="w")

tk.Label(hint_row, text="💡  New here?  No account yet? →",
         font=(FF, 9), bg="#2a2d1e", fg="#c8d87a").pack(side="left")

reg_hint_link = tk.Label(hint_row, text="Register here",
                          font=(FF, 9, "bold", "underline"),
                          bg="#2a2d1e", fg="#a8f07a", cursor="hand2")
reg_hint_link.pack(side="left", padx=(4, 0))
reg_hint_link.bind("<Button-1>", lambda _: open_register())

# ── Card ───────────────────────────────────────────────────────────────────────
card = tk.Frame(root, bg=T["card"], padx=36, pady=28)
card.pack(padx=40, pady=12, fill="x")

username_var = tk.StringVar()
password_var = tk.StringVar()
error_var    = tk.StringVar()

tk.Label(card, text="Username", font=(FF, 10),
         bg=T["card"], fg=T["subtext"]).pack(anchor="w", pady=(0, 2))
u_entry = _make_entry(card, username_var)

tk.Label(card, text="Password", font=(FF, 10),
         bg=T["card"], fg=T["subtext"]).pack(anchor="w", pady=(10, 2))
p_entry = _make_entry(card, password_var, show="•")

# Error message
tk.Label(card, textvariable=error_var, font=(FF, 9),
         bg=T["card"], fg=T["red"], wraplength=320).pack(pady=(10, 0))

# ── Sign-In Button ─────────────────────────────────────────────────────────────
login_btn = tk.Button(
    card, text="Sign In", font=(FF, 11, "bold"),
    bg=T["accent"], fg="white",
    activebackground=T["accent_hover"], activeforeground="white",
    relief="flat", cursor="hand2", command=login
)
login_btn.pack(fill="x", ipady=10, pady=(16, 0))
login_btn.bind("<Enter>", lambda _: login_btn.config(bg=T["accent_hover"]))
login_btn.bind("<Leave>", lambda _: login_btn.config(bg=T["accent"]))

# ── Register Link ──────────────────────────────────────────────────────────────
bottom = tk.Frame(root, bg=T["bg"])
bottom.pack(pady=8)

tk.Label(bottom, text="Don't have an account?", font=(FF, 9),
         bg=T["bg"], fg=T["subtext"]).pack(side="left")

reg_link = tk.Label(bottom, text=" Register here", font=(FF, 9, "underline"),
                    bg=T["bg"], fg=T["accent"], cursor="hand2")
reg_link.pack(side="left")
reg_link.bind("<Button-1>", lambda _: open_register())

# ── Key bindings ───────────────────────────────────────────────────────────────
root.bind("<Return>", lambda _: login())
u_entry.focus_set()

root.mainloop()