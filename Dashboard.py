import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import sys 
from datetime import datetime

DB_NAME = "users.db"

def connect_db():
  return sqlite3.connect(DB_NAME)

def create_transactions_table():
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("""
      CREATE TABLE IF NOT EXISTS transactions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          type TEXT NOT NULL,
          amount REAL NOT NULL,
          category TEXT NOT NULL,
          date TEXT NOT NULL,
          note TEXT
      )
    """)
  conn.commit()
  conn.close()

def get_current_month():
  return datetime.now().strftime("%Y-%m")

def get_total_income_this_month():
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("""
      SELECT IFNULL(SUM(amount), 0)
      FROM transactions
      WHERE type = 'Income' AND substr(date, 1, 7) = ?
    """, (get_current_month(),))
  total = cursor.fetchone()[0]
  conn.close()
  return total

def get_total_expenses_this_month():
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("""
      SELECT IFNULL(SUM(amount), 0)
      FROM transactions
      WHERE type = 'Expense' AND substr(date, 1, 7) = ?
    """, (get_current_month(),))
  total = cursor.fetchone()[0]
  conn.close()
  return total

def get_balance():
  conn = connect_db()
  cursor = conn.cursor()

  cursor.execute("SELECT IFNULL(SUM(amount), 0) FROM transactions WHERE type = 'Income'")
  total_income = cursor.fetchone()[0]

  cursor.execute("SELECT IFNULL(SUM(amount), 0) FROM transactions WHERE type = 'Expense'")
  total_expense = cursor.fetchone()[0]

  conn.close()
  return total_income - total_expense

def get_savings():
  return get_total_income_this_month() - get_total_expenses_this_month()

def get_recent_transactions(limit=5):
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("""
      SELECT type, amount, category, date, IFNULL(note, '') 
      FROM transactions
      ORDER BY date DESC, id DESC
      LIMIT ?
    """, (limit,))
  rows = cursor.fetchall()
  conn.close()
  return rows

def get_category_summary():
  conn = connect_db()
  cursor = conn.cursor()
  cursor.execute("""
      SELECT category, IFNULL(SUM(amount), 0)
      FROM transactions 
      WHERE type = 'Expense' AND substr(date, 1, 7) = ?
      GROUP BY category
      ORDER BY SUM(amount) DESC
      LIMIT 5
    """, (get_current_month(),))
  rows = cursor.fetchall()
  conn.close()
  return rows

def get_budget_alert():
  expense = get_total_expenses_this_month()
  budget_limit = 2000 # simple example budget

  if expense > budget_limit:
    return f"Alert: You reached your monthly budget of ${budget_limit:.2f}"
  elif expense > budget_limit * 0.8:
    return f"Warning: You used 80% of your budget (${expense:.2f}/${budget_limit:.2f})"
  else:
    return "Budget status is healthy."
  
class Dashboard(tk.Tk):
  def __init__(self):
    super().__init__()
    self.title("Dashboard")
    self.geometry("1000x700")
    self.resizable(False, False)

    create_transactions_table()

    title = tk.Label(self, text="Personal Finance Tracker Dashboard", font=("Arial", 20, "bold"))
    title.pack(pady=15)

    self.create_top_cards()
    self.create_middle_section()
    self.create_bottom_section()
    self.create_buttons()

    self.refresh_data()

  def create_top_cards(self):
    self.top_frame = tk.Frame(self)
    self.top_frame.pack(pady=10)

    self.balance_label = self.create_card(self.top_frame, "Balance ", 0)
    self.income_label = self.create_card(self.top_frame, "Income ", 1)
    self.expense_label = self.create_card(self.top_frame, "Expenses ", 2)
    self.savings_label = self.create_card(self.top_frame, "Savings ", 3)

  def create_card(self, parent, title, column):
    frame = tk.Frame(parent, bd=2, relief="groove", padx=20, pady=15, bg="white")
    frame.grid(row=0, column=column, padx=10)

    tk.Label(frame, text=title, font=("Arial", 14, "bold"), bg="white").pack()
    value_label = tk.Label(frame, text="$0.00", font=("Arial", 16), fg="blue", bg="white")
    value_label.pack(pady=5)
    return value_label
  
  def create_middle_section(self):
    middle_frame = tk.Frame(self)
    middle_frame.pack(pady=15, fill="x", padx=20)

    alert_title = tk.Label(middle_frame, text="Budget Alert", font=("Arial", 14, "bold"))
    alert_title.pack(anchor="w")

    self.alert_label = tk.Label(middle_frame, text="", font=("Arial", 11), fg="red")
    self.alert_label.pack(anchor="w", pady=(0, 10))

    recent_title = tk.Label(middle_frame, text="Recent 5 Transactions", font=("Arial", 14, "bold"))
    recent_title.pack(anchor="w")

    columns = ("Type", "Amount", "Category", "Date", "Note")
    self.tree = ttk.Treeview(middle_frame, columns=columns, show="headings", height=6)

    for col in columns:
      self.tree.heading(col, text=col)
      self.tree.column(col, width=170 if col == "Note" else 120)

    self.tree.pack(fill="x", pady=10) 

  def create_bottom_section(self):
    bottom_frame = tk.Frame(self)
    bottom_frame.pack(pady=10, fill="x", padx=20)

    tk.Label(bottom_frame, text="Quick Category Summary (Top 5)", font=("Arial", 14, "bold")).pack(anchor="w")

    self.summary_text = tk.Text(bottom_frame, height=8, width=110)
    self.summary_text.pack(pady=10)
    self.summary_text.config(state="disabled")

  def create_buttons(self):
    button_frame = tk.Frame(self)
    button_frame.pack(pady=20)

    tk.Button(button_frame, text="Add Income", width=15, command=lambda: self.open_transaction("Income")).grid(row=0, column=0, padx=5)
    tk.Button(button_frame, text="Add Expense", width=15, command=lambda: self.open_transaction("Expense")).grid(row=0, column=1, padx=5)
    tk.Button(button_frame, text="View History", width=15, command=self.view_history).grid(row=0, column=2, padx=5, pady=5)
    tk.Button(button_frame, text="Budgets", width=15, command=self.show_budgets).grid(row=0, column=3, padx=5, pady=5)
    tk.Button(button_frame, text="Reports", width=15, command=self.show_reports).grid(row=0, column=4, padx=5, pady=5)
    tk.Button(button_frame, text="Logout", width=15, command=self.logout).grid(row=0, column=5, padx=5, pady=5)

  def refresh_data(self):
    self.balance_label.config(text=f"${get_balance():.2f}")
    self.income_label.config(text=f"${get_total_income_this_month():.2f}")
    self.expense_label.config(text=f"${get_total_expenses_this_month():.2f}")
    self.savings_label.config(text=f"${get_savings():.2f}")

    self.alert_label.config(text=get_budget_alert())

    for item in self.tree.get_children():
      self.tree.delete(item)

    for row in get_recent_transactions():
      self.tree.insert("", "end", values=row)

    summary = get_category_summary()
    self.summary_text.config(state="normal")
    self.summary_text.delete(1.0, tk.END)

    if summary:
      for category, total in summary:
        self.summary_text.insert(tk.END, f"{category}: ${total:.2f}\n")
    else:
      self.summary_text.insert(tk.END, "No expense data for this month yet.")

    self.summary_text.config(state="disabled")

  def open_transaction(self, transaction_type):
    self.destroy()
    subprocess.Popen([sys.executable, "Transaction.py", transaction_type])

  def view_history(self):
    messagebox.showinfo("View History", "History page can be added next.")
  
  def show_budgets(self):
    messagebox.showinfo("Budgets", "Budget management can be added next.")
  
  def show_reports(self):
    messagebox.showinfo("Reports", "Report page can be added next.")

  def logout(self):
    self.destroy()
    subprocess.Popen([sys.executable, "Pages/Login.py"])

if __name__ == "__main__":
  app = Dashboard()
  app.mainloop()


# Reset 0 when started a new one
# it's gonna be go Transaction.py first 
# Reset Transaction 0
# add ui
# 