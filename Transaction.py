import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import sys
from datetime import datetime

DB_NAME = "users.db"

EXPENSE_CATEGORISE = [
  "Food",
  "Rent",
  "Transport",
  "Shopping",
  "Bill",
  "Entertainment",
  "Health",
  "Other"
]

INCOME_CATEGORISE = [
  "Salary",
  "Freelance",
  "Gift",
  "Bonus",
  "Other"
]

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

class TransactionApp(tk.Tk):
  def __init__(self, default_type="Income"):
    super().__init__()
    self.title("Add Transaction")
    self.geometry("700x550")
    self.resizable(False, False)
    
    create_transactions_table()

    self.default_type = default_type

    title = tk.Label(self, text="Add Transaction", font=("Arial", 18, "bold"))
    title.pack(pady=15)

    form_frame = tk.Frame(self)
    form_frame.pack(pady=10)

    tk.Label(form_frame, text="Type:").grid(row=0, column=0, sticky="w", pady=5 )
    self.type_var = tk.StringVar(value=self.default_type)
    self.type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, state="readonly", width=27, values=["Income", "Expense"])
    self.type_combo.grid(row=0, column=1, pady=5)
    self.type_combo.bind("<<ComboboxSelected>>", self.update_categories)

    tk.Label(form_frame, text="Amount:").grid(row=1, column=0, sticky="w", pady=5)
    self.amount_entry = tk.Entry(form_frame, width=30)
    self.amount_entry.grid(row=1, column=1, pady=5)

    tk.Label(form_frame, text="Category:").grid(row=2, column=0, sticky="w", pady=5)
    self.category_var = tk.StringVar()
    self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var, state="readonly", width=27)
    self.category_combo.grid(row=2, column=1, pady=5)

    tk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=3, column=0, sticky="w", pady=5)
    self.date_entry = tk.Entry(form_frame, width=30)
    self.date_entry.grid(row=3, column=1, pady=5)
    self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    tk.Label(form_frame, text="Note (optional):").grid(row=4, column=0, sticky="w", pady=5)
    self.note_entry = tk.Entry(form_frame, width=30)
    self.note_entry.grid(row=4, column=1, pady=5)

    self.error_label = tk.Label(self, text="", fg="red", font=("Arial", 10))
    self.error_label.pack(pady=10)

    button_frame = tk.Frame(self)
    button_frame.pack(pady=20)

    tk.Button(button_frame, text="Save", width=15, command=self.add_transaction).grid(row=0, column=0, padx=10)
    tk.Button(button_frame, text="Cancel", width=15, command=self.destroy).grid(row=0, column=1, padx=10)

    self.update_categories()
    self.create_table()
    self.load_transactions()


  def update_categories(self, event=None):
    selected_type = self.type_var.get()
    if selected_type == "Income":
      self.category_combo["values"] = INCOME_CATEGORISE
      self.category_combo.set(INCOME_CATEGORISE[0])
    else:
      self.category_combo["values"] = EXPENSE_CATEGORISE
      self.category_combo.set(EXPENSE_CATEGORISE[0])

  def create_table(self):
    frame = tk.Frame(self)
    frame.pack(pady=10)

    columns = ("ID", "Type", "Amount", "Category", "Date", "Note")

    self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)

    for col in columns:
      self.tree.heading(col, text=col)
      self.tree.column(col, width=100)

    self.tree.pack()

    btn_frame = tk.Frame(self)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Delete Selected", width=15, command=self.delete_transaction).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Refresh", width=15, command=self.load_transactions).grid(row=0, column=1, padx=10)

  def add_transaction(self):
    try:
      amount = float(self.amount_entry.get())
      if amount <= 0:
        raise ValueError
    except:
      messagebox.showerror("Error", "Invalid amount. Please enter a valid number.")
      return
    
    date = self.date_entry.get()

    try:
      datetime.strptime(date, "%Y-%m-%d")
    except:
      messagebox.showerror("Error", "Invalid date format.")
      return
    
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (type, amount, category, date, note)
        VALUES (?, ?, ?, ?, ?)
      """, (
            self.type_var.get(),
            amount,
            self.category_var.get(),
            date,
            self.note_entry.get()
        ))
    
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Transaction added successfully!")
    self.clear_form()
    self.load_transactions()

  def load_transactions(self):
    for row in self.tree.get_children():
      self.tree.delete(row)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = cursor.fetchall()

    for row in rows:
      self.tree.insert("", "end", values=row)

    conn.close()

  def delete_transaction(self):
    selected = self.tree.selection()
    if not selected:
      messagebox.showwarning("Warning", "Select a transaction")
      return

    item = self.tree.item(selected[0])
    transaction_id = item["values"][0]

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

    conn.commit()
    conn.close()

    messagebox.showinfo("Deleted", "Transaction deleted successfully.")
    self.load_transactions()
  
  def clear_form(self):
    self.amount_entry.delete(0, tk.END)
    self.note_entry.delete(0, tk.END)
    self.date_entry.delete(0, tk.END)
    self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

if __name__ == "__main__":
  app = TransactionApp()
  app.mainloop()