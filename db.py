"""
db.py — Shared module for Personal Finance Tracker.
Centralises DB connection, schema, auth helpers, theme, and all query functions.
"""

import sqlite3
import hashlib
import os
import calendar
from datetime import datetime, date

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME  = os.path.join(ROOT_DIR, "users.db")

# ── Design System (Dark Theme) ─────────────────────────────────────────────────
THEME = {
    "bg":          "#1a1d2e",   # main window background
    "card":        "#252839",   # card / panel background
    "card2":       "#2d3147",   # slightly lighter card (hover states)
    "input_bg":    "#363952",   # entry & combobox background
    "border":      "#464b6e",   # subtle borders
    "accent":      "#6c63ff",   # primary accent (purple)
    "accent_hover":"#5a52d5",   # accent on hover
    "green":       "#2ecc71",   # income / positive values
    "red":         "#e74c3c",   # expense / negative values
    "yellow":      "#f39c12",   # warning / near-limit
    "text":        "#e8e8f0",   # primary text
    "subtext":     "#8b8fa8",   # secondary / label text
    "row_alt":     "#2a2d40",   # alternating Treeview rows
}

FONT = "Segoe UI"

# ── Database Connection ────────────────────────────────────────────────────────
def connect_db():
    """Return a new SQLite connection to the shared database."""
    return sqlite3.connect(DB_NAME)


def create_all_tables():
    """Create all required tables and run schema migrations if needed."""
    conn = connect_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt          TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER,
            type     TEXT NOT NULL,
            amount   REAL NOT NULL,
            category TEXT NOT NULL,
            date     TEXT NOT NULL,
            note     TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            user_id       INTEGER PRIMARY KEY,
            monthly_limit REAL NOT NULL DEFAULT 2000.0
        )
    """)

    # Migration: add user_id column to transactions if it's missing (legacy DB)
    c.execute("PRAGMA table_info(transactions)")
    if "user_id" not in [row[1] for row in c.fetchall()]:
        c.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")

    conn.commit()
    conn.close()


# ── Auth Helpers ───────────────────────────────────────────────────────────────
def hash_password(password: str, salt: bytes = None):
    """
    Hash a password with PBKDF2-SHA256.
    Returns (hash_hex, salt_hex). Generates a random 16-byte salt if not given.
    """
    if salt is None:
        salt = os.urandom(16)
    pw_bytes = password.encode("utf-8")
    h = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt, 100_000)
    return h.hex(), salt.hex()


def verify_password(stored_hash: str, stored_salt: str, entered: str) -> bool:
    """Return True if entered password matches the stored hash."""
    salt_bytes = bytes.fromhex(stored_salt)
    entered_hash, _ = hash_password(entered, salt_bytes)
    return entered_hash == stored_hash


# ── Budget Helpers ─────────────────────────────────────────────────────────────
def get_user_budget(user_id: int) -> float:
    """Return the user's monthly budget limit (default $2000)."""
    if user_id is None:
        return 2000.0
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT monthly_limit FROM budgets WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 2000.0


def set_user_budget(user_id: int, amount: float):
    """Insert or update the user's monthly budget limit."""
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO budgets (user_id, monthly_limit) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET monthly_limit = excluded.monthly_limit
    """, (user_id, amount))
    conn.commit()
    conn.close()


# ── Date Helpers ───────────────────────────────────────────────────────────────
def get_current_month() -> str:
    """Return current month as 'YYYY-MM' string."""
    return datetime.now().strftime("%Y-%m")


# ── Query Functions ────────────────────────────────────────────────────────────
def get_total_income(user_id, month: str = None) -> float:
    """Sum of income transactions for a user in a given month (default: current month)."""
    if user_id is None:
        return 0.0
    month = month or get_current_month()
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        SELECT IFNULL(SUM(amount), 0) FROM transactions
        WHERE type = 'Income' AND substr(date, 1, 7) = ? AND user_id = ?
    """, (month, user_id))
    total = c.fetchone()[0]
    conn.close()
    return total


def get_total_expenses(user_id, month: str = None) -> float:
    """Sum of expense transactions for a user in a given month (default: current month)."""
    if user_id is None:
        return 0.0
    month = month or get_current_month()
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        SELECT IFNULL(SUM(amount), 0) FROM transactions
        WHERE type = 'Expense' AND substr(date, 1, 7) = ? AND user_id = ?
    """, (month, user_id))
    total = c.fetchone()[0]
    conn.close()
    return total


def get_all_time_balance(user_id) -> float:
    """All-time net balance (total income − total expenses) for a user."""
    if user_id is None:
        return 0.0
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT IFNULL(SUM(amount),0) FROM transactions WHERE type='Income'  AND user_id=?", (user_id,))
    inc = c.fetchone()[0]
    c.execute("SELECT IFNULL(SUM(amount),0) FROM transactions WHERE type='Expense' AND user_id=?", (user_id,))
    exp = c.fetchone()[0]
    conn.close()
    return inc - exp


def get_recent_transactions(user_id, limit: int = 10):
    """Return the N most recent transactions for a user."""
    if user_id is None:
        return []
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        SELECT date, amount, category, type, IFNULL(note, '')
        FROM transactions WHERE user_id = ?
        ORDER BY date DESC, id DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_transactions(user_id):
    """Return all transactions for a user, newest first."""
    if user_id is None:
        return []
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, type, amount, category, date, IFNULL(note, '')
        FROM transactions WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_category_summary(user_id, month: str = None):
    """Return (category, total) pairs for expenses, grouped by category."""
    if user_id is None:
        return []
    month = month or get_current_month()
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        SELECT category, IFNULL(SUM(amount), 0)
        FROM transactions
        WHERE type = 'Expense' AND substr(date, 1, 7) = ? AND user_id = ?
        GROUP BY category ORDER BY SUM(amount) DESC
    """, (month, user_id))
    rows = c.fetchall()
    conn.close()
    return rows


def get_monthly_summary(user_id, months: int = 6):
    """
    Return [(month_label, income, expense), ...] for the last N months,
    oldest first. No external dependencies required.
    """
    if user_id is None:
        return []

    result = []
    now = datetime.now()
    y, m = now.year, now.month

    # Build list of (year, month) pairs going back N months
    month_list = []
    for _ in range(months):
        month_list.insert(0, (y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1

    for yr, mo in month_list:
        month_str = f"{yr}-{mo:02d}"
        label     = date(yr, mo, 1).strftime("%b")
        income    = get_total_income(user_id, month_str)
        expense   = get_total_expenses(user_id, month_str)
        result.append((label, income, expense))

    return result


def get_month_overview(user_id):
    """Return a dict of key stats for the current month dashboard display."""
    now           = datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    budget        = get_user_budget(user_id)
    spent         = get_total_expenses(user_id)
    income        = get_total_income(user_id)
    daily_avg     = spent / now.day if now.day > 0 else 0.0

    return {
        "month_name": now.strftime("%B %Y"),
        "start_date": f"{now.year}-{now.month:02d}-01",
        "end_date":   f"{now.year}-{now.month:02d}-{days_in_month:02d}",
        "budget":     budget,
        "spent":      spent,
        "income":     income,
        "left":       max(budget - spent, 0),
        "daily_avg":  daily_avg,
        "balance":    get_all_time_balance(user_id),
        "savings":    income - spent,
    }
