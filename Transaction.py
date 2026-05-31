"""
Transaction.py — Add, view, and delete transactions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import sys
import os
from datetime import datetime

# ── Paths & shared module ──────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from db import (THEME as T, FONT as FF,
                connect_db, create_all_tables,
                get_all_transactions)

# ── Categories ─────────────────────────────────────────────────────────────────
EXPENSE_CATEGORIES = [
    "Food", "Rent", "Transport", "Shopping",
    "Bill", "Entertainment", "Health", "Other"
]
INCOME_CATEGORIES = [
    "Salary", "Freelance", "Gift", "Bonus", "Other"
]


# ── Styled helper ──────────────────────────────────────────────────────────────
def _make_entry(parent, var=None, show=None, width=None):
    """Dark-theme Entry with focus highlight border."""
    border = tk.Frame(parent, bg=T["border"], padx=1, pady=1)
    kw = dict(bg=T["input_bg"], fg=T["text"], insertbackground=T["accent"],
              relief="flat", font=(FF, 11), bd=0)
    if var:
        kw["textvariable"] = var
    if show:
        kw["show"] = show
    entry = tk.Entry(border, **kw)
    entry.pack(fill="x", ipady=7, padx=6)
    border.pack(fill="x", pady=(0, 2))

    entry.bind("<FocusIn>",  lambda _: border.config(bg=T["accent"]))
    entry.bind("<FocusOut>", lambda _: border.config(bg=T["border"]))
    return entry, border


class TransactionApp(tk.Tk):
    def __init__(self, default_type: str = "Income", user_id=None):
        super().__init__()
        self.user_id      = user_id
        self.default_type = default_type

        create_all_tables()

        self.title("Personal Finance Tracker — Transactions")
        self.geometry("860x680")
        self.resizable(False, False)
        self.configure(bg=T["bg"])
        self._center()
        self._apply_styles()
        self._build_ui()
        self._load_transactions()

    # ── Setup ──────────────────────────────────────────────────────────────────
    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"860x680+{(sw - 860) // 2}+{(sh - 680) // 2}")

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=T["card"], foreground=T["text"],
                         fieldbackground=T["card"], rowheight=28, font=(FF, 10))
        style.configure("Dark.Treeview.Heading",
                         background=T["card2"], foreground=T["subtext"],
                         font=(FF, 10, "bold"), relief="flat")
        style.map("Dark.Treeview",
                  background=[("selected", T["accent"])],
                  foreground=[("selected", "white")])
        style.map("Dark.Treeview.Heading",
                  background=[("active", T["card2"])])
        style.configure("Dark.Vertical.TScrollbar",
                         background=T["card2"], troughcolor=T["card"],
                         arrowcolor=T["subtext"])
        style.configure("Dark.TCombobox",
                         fieldbackground=T["input_bg"],
                         background=T["input_bg"],
                         foreground=T["text"],
                         selectbackground=T["accent"])
        self.option_add("*TCombobox*Listbox.background", T["card2"])
        self.option_add("*TCombobox*Listbox.foreground", T["text"])

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=T["card"], pady=12)
        header.pack(fill="x")
        tk.Label(header, text="💸  Transactions", font=(FF, 15, "bold"),
                 bg=T["card"], fg=T["text"]).pack(side="left", padx=20)

        dash_btn = tk.Button(
            header, text="← Dashboard", font=(FF, 10),
            bg=T["card2"], fg=T["accent"],
            activebackground=T["border"], activeforeground=T["accent"],
            relief="flat", cursor="hand2", command=self.open_dashboard,
            padx=12, pady=5
        )
        dash_btn.pack(side="right", padx=20)

        # Main area: form (left) | table (right)
        main = tk.Frame(self, bg=T["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=12)

        self._build_form(main)
        self._build_table(main)

    def _build_form(self, parent):
        form_card = tk.Frame(parent, bg=T["card"], padx=20, pady=20, width=280)
        form_card.pack(side="left", fill="y", padx=(0, 12))
        form_card.pack_propagate(False)

        tk.Label(form_card, text="Add Transaction", font=(FF, 12, "bold"),
                 bg=T["card"], fg=T["text"]).pack(anchor="w", pady=(0, 14))

        def lbl(text):
            tk.Label(form_card, text=text, font=(FF, 10),
                     bg=T["card"], fg=T["subtext"]).pack(anchor="w", pady=(8, 2))

        # Type
        lbl("Type")
        self.type_var = tk.StringVar(value=self.default_type)
        self.type_combo = ttk.Combobox(
            form_card, textvariable=self.type_var,
            values=["Income", "Expense"], state="readonly",
            style="Dark.TCombobox", font=(FF, 11)
        )
        self.type_combo.pack(fill="x")
        self.type_combo.bind("<<ComboboxSelected>>", self._update_categories)

        # Amount
        lbl("Amount ($)")
        self.amount_var = tk.StringVar()
        self.amount_entry, _ = _make_entry(form_card, self.amount_var)

        # Category
        lbl("Category")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            form_card, textvariable=self.category_var,
            state="readonly", style="Dark.TCombobox", font=(FF, 11)
        )
        self.category_combo.pack(fill="x")

        # Date
        lbl("Date (YYYY-MM-DD)")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry, _ = _make_entry(form_card, self.date_var)

        # Note
        lbl("Note (optional)")
        self.note_var = tk.StringVar()
        self.note_entry, _ = _make_entry(form_card, self.note_var)

        # Error label
        self.error_var = tk.StringVar()
        tk.Label(form_card, textvariable=self.error_var, font=(FF, 9),
                 bg=T["card"], fg=T["red"], wraplength=230).pack(pady=(8, 0))

        # Save button
        save_btn = tk.Button(
            form_card, text="Save Transaction", font=(FF, 11, "bold"),
            bg=T["accent"], fg="white",
            activebackground=T["accent_hover"], activeforeground="white",
            relief="flat", cursor="hand2", command=self._add_transaction
        )
        save_btn.pack(fill="x", ipady=10, pady=(12, 0))
        save_btn.bind("<Enter>", lambda _: save_btn.config(bg=T["accent_hover"]))
        save_btn.bind("<Leave>", lambda _: save_btn.config(bg=T["accent"]))

        self._update_categories()

    def _build_table(self, parent):
        right = tk.Frame(parent, bg=T["card"])
        right.pack(side="left", fill="both", expand=True)

        # Table header
        tbl_header = tk.Frame(right, bg=T["card"], pady=12, padx=14)
        tbl_header.pack(fill="x")
        tk.Label(tbl_header, text="Transaction History", font=(FF, 12, "bold"),
                 bg=T["card"], fg=T["text"]).pack(side="left")

        del_btn = tk.Button(
            tbl_header, text="🗑  Delete Selected", font=(FF, 9),
            bg=T["red"], fg="white",
            activebackground="#c0392b", activeforeground="white",
            relief="flat", cursor="hand2", command=self._delete_transaction,
            padx=10, pady=4
        )
        del_btn.pack(side="right")

        ref_btn = tk.Button(
            tbl_header, text="↺ Refresh", font=(FF, 9),
            bg=T["card2"], fg=T["subtext"],
            activebackground=T["border"],
            relief="flat", cursor="hand2", command=self._load_transactions,
            padx=10, pady=4
        )
        ref_btn.pack(side="right", padx=8)

        # Treeview
        tree_frame = tk.Frame(right, bg=T["card"])
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        cols = ("ID", "Type", "Amount", "Category", "Date", "Note")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            height=18, style="Dark.Treeview"
        )
        col_widths = {"ID": 50, "Type": 90, "Amount": 100,
                      "Category": 130, "Date": 110, "Note": 180}
        for col in cols:
            self.tree.heading(col, text=col)
            anchor = "center" if col != "Note" else "w"
            self.tree.column(col, width=col_widths[col], anchor=anchor)

        self.tree.tag_configure("income",  background="#1e3a2f", foreground=T["green"])
        self.tree.tag_configure("expense", background="#3a1e2a", foreground=T["red"])

        sb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.tree.yview,
                            style="Dark.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ── Logic ──────────────────────────────────────────────────────────────────
    def _update_categories(self, _event=None):
        if self.type_var.get() == "Income":
            self.category_combo["values"] = INCOME_CATEGORIES
            self.category_combo.set(INCOME_CATEGORIES[0])
        else:
            self.category_combo["values"] = EXPENSE_CATEGORIES
            self.category_combo.set(EXPENSE_CATEGORIES[0])

    def _add_transaction(self):
        self.error_var.set("")

        # Validate amount
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            self.error_var.set("⚠  Enter a valid positive number for amount.")
            return

        # Validate date
        date_str = self.date_var.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.error_var.set("⚠  Date must be in YYYY-MM-DD format.")
            return

        conn = connect_db()
        c    = conn.cursor()
        c.execute("""
            INSERT INTO transactions (user_id, type, amount, category, date, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            self.user_id,
            self.type_var.get(),
            amount,
            self.category_var.get(),
            date_str,
            self.note_var.get().strip()
        ))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Transaction saved successfully! ✔")
        self._clear_form()
        self._load_transactions()

    def _load_transactions(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for row in get_all_transactions(self.user_id):
            t_id, t_type, amount, category, date, note = row
            tag = "income" if t_type == "Income" else "expense"
            prefix = "+" if t_type == "Income" else "-"
            self.tree.insert("", "end",
                              values=(t_id, t_type, f"{prefix}${amount:.2f}",
                                      category, date, note),
                              tags=(tag,))

    def _delete_transaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Nothing Selected", "Please select a transaction to delete.")
            return

        item = self.tree.item(selected[0])
        transaction_id = item["values"][0]

        if not messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete this transaction?"):
            return

        conn = connect_db()
        c    = conn.cursor()
        c.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        conn.close()

        messagebox.showinfo("Deleted", "Transaction deleted successfully.")
        self._load_transactions()

    def _clear_form(self):
        self.amount_var.set("")
        self.note_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))

    def open_dashboard(self):
        self.destroy()
        script = os.path.join(ROOT_DIR, "Dashboard.py")
        args   = [sys.executable, script]
        if self.user_id is not None:
            args.append(str(self.user_id))
        subprocess.Popen(args)


if __name__ == "__main__":
    transaction_type = sys.argv[1] if len(sys.argv) > 1 else "Income"
    user_id = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
    app = TransactionApp(transaction_type, user_id)
    app.mainloop()