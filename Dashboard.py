"""
Dashboard.py — Main dashboard for Personal Finance Tracker.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

# ── Paths & shared module ──────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from db import (THEME as T, FONT as FF,
                create_all_tables,
                get_month_overview, get_recent_transactions,
                get_category_summary,
                get_user_budget, set_user_budget, get_total_expenses)

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Dashboard(tk.Tk):
    def __init__(self, user_id=None):
        super().__init__()
        self.user_id           = user_id
        self.transaction_limit = 10

        create_all_tables()

        self.title("Personal Finance Tracker — Dashboard")
        self.geometry("1360x820")
        self.resizable(False, False)
        self.configure(bg=T["bg"])
        self._center()
        self._apply_styles()
        self._build_ui()
        self.refresh_data()

    # ── Setup ──────────────────────────────────────────────────────────────────
    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1360x820+{(sw - 1360) // 2}+{(sh - 820) // 2}")

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Dark.Treeview",
                         background=T["card"], foreground=T["text"],
                         fieldbackground=T["card"], rowheight=27, font=(FF, 10))
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

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_stat_cards()
        self._build_main_area()
        self._build_bottom_bar()

    def _build_header(self):
        header = tk.Frame(self, bg=T["card"], pady=13)
        header.pack(fill="x")

        tk.Label(header, text="💰  Personal Finance Tracker",
                 font=(FF, 15, "bold"), bg=T["card"], fg=T["text"]
                 ).pack(side="left", padx=20)

        btn_data = [
            ("📊  Reports",   self.show_reports,  T["card2"]),
            ("💰  Budget",    self.show_budgets,   T["card2"]),
            ("⎋  Logout",    self.logout,          "#3a1e2a"),
        ]
        for text, cmd, bg in reversed(btn_data):
            b = tk.Button(
                header, text=text, font=(FF, 10),
                bg=bg, fg=T["text"],
                activebackground=T["border"], activeforeground=T["text"],
                relief="flat", cursor="hand2", command=cmd,
                padx=14, pady=6
            )
            b.pack(side="right", padx=6)

    def _build_stat_cards(self):
        self.cards_frame = tk.Frame(self, bg=T["bg"])
        self.cards_frame.pack(fill="x", padx=18, pady=14)

        card_defs = [
            ("balance",  "Net Balance",          "💳", T["accent"]),
            ("income",   "This Month Income",    "📈", T["green"]),
            ("expenses", "This Month Expenses",  "📉", T["red"]),
            ("savings",  "Monthly Savings",      "💵", T["yellow"]),
        ]
        self.stat_labels = {}
        for key, title, icon, color in card_defs:
            card = tk.Frame(self.cards_frame, bg=T["card"], padx=18, pady=14)
            card.pack(side="left", fill="x", expand=True, padx=7)

            tk.Label(card, text=f"{icon}  {title}", font=(FF, 9),
                     bg=T["card"], fg=T["subtext"]).pack(anchor="w")
            lbl = tk.Label(card, text="$0.00", font=(FF, 18, "bold"),
                           bg=T["card"], fg=color)
            lbl.pack(anchor="w", pady=(4, 0))
            self.stat_labels[key] = lbl

    def _build_main_area(self):
        main = tk.Frame(self, bg=T["bg"])
        main.pack(fill="both", expand=True, padx=18, pady=(0, 6))

        # ── Left: Transaction table ────────────────────────────────────────────
        left = tk.Frame(main, bg=T["card"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tx_hdr = tk.Frame(left, bg=T["card"], pady=12, padx=14)
        tx_hdr.pack(fill="x")
        tk.Label(tx_hdr, text="Recent Transactions", font=(FF, 12, "bold"),
                 bg=T["card"], fg=T["text"]).pack(side="left")

        btn_box = tk.Frame(tx_hdr, bg=T["card"])
        btn_box.pack(side="right")
        for text, ttype, color in [
            ("+ Income",  "Income",  T["green"]),
            ("+ Expense", "Expense", T["red"])
        ]:
            b = tk.Button(
                btn_box, text=text, font=(FF, 9, "bold"),
                bg=color, fg="white", activebackground=color,
                relief="flat", cursor="hand2", padx=12, pady=4,
                command=lambda t=ttype: self.open_transaction(t)
            )
            b.pack(side="left", padx=4)

        # Treeview
        tree_wrap = tk.Frame(left, bg=T["card"])
        tree_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        cols = ("Date", "Amount", "Category", "Type", "Note")
        self.tree = ttk.Treeview(
            tree_wrap, columns=cols, show="headings",
            height=18, style="Dark.Treeview"
        )
        col_widths = {"Date": 115, "Amount": 110,
                      "Category": 145, "Type": 95, "Note": 215}
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[col],
                             anchor="center" if col != "Note" else "w")

        self.tree.tag_configure("income",  background="#1e3a2f", foreground=T["green"])
        self.tree.tag_configure("expense", background="#3a1e2a", foreground=T["red"])

        sb = ttk.Scrollbar(tree_wrap, orient="vertical",
                            command=self.tree.yview,
                            style="Dark.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Load more
        more = tk.Button(
            left, text="Load More ↓", font=(FF, 9),
            bg=T["card2"], fg=T["subtext"],
            activebackground=T["border"],
            relief="flat", cursor="hand2",
            command=self.load_more_transactions
        )
        more.pack(pady=(0, 10))

        # ── Right: Donut + Breakdown ───────────────────────────────────────────
        right = tk.Frame(main, bg=T["bg"], width=330)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        # Donut chart card
        donut_card = tk.Frame(right, bg=T["card"], pady=12)
        donut_card.pack(fill="x", pady=(0, 8))
        tk.Label(donut_card, text="Budget Used This Month",
                 font=(FF, 11, "bold"), bg=T["card"], fg=T["text"]
                 ).pack(padx=14, anchor="w", pady=(0, 4))
        self.donut_holder = tk.Frame(donut_card, bg=T["card"])
        self.donut_holder.pack(fill="x")

        # Breakdown card
        bk_card = tk.Frame(right, bg=T["card"])
        bk_card.pack(fill="both", expand=True)
        tk.Label(bk_card, text="Expense Breakdown",
                 font=(FF, 11, "bold"), bg=T["card"], fg=T["text"]
                 ).pack(padx=14, pady=(12, 4), anchor="w")

        self.breakdown_tree = ttk.Treeview(
            bk_card,
            columns=("Category", "Amount", "Pct"),
            show="headings", height=10,
            style="Dark.Treeview"
        )
        self.breakdown_tree.heading("Category", text="Category")
        self.breakdown_tree.heading("Amount",   text="Amount")
        self.breakdown_tree.heading("Pct",      text="%")
        self.breakdown_tree.column("Category", width=120, anchor="w")
        self.breakdown_tree.column("Amount",   width=100, anchor="center")
        self.breakdown_tree.column("Pct",      width=65,  anchor="center")
        self.breakdown_tree.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _build_bottom_bar(self):
        bar = tk.Frame(self, bg=T["bg"], pady=8)
        bar.pack(fill="x", padx=18)

        tk.Button(
            bar, text="📋  View All Transactions", font=(FF, 10),
            bg=T["card"], fg=T["text"],
            activebackground=T["card2"],
            relief="flat", cursor="hand2",
            command=self.view_history,
            padx=16, pady=7
        ).pack(side="left")

    # ── Data refresh ───────────────────────────────────────────────────────────
    def refresh_data(self):
        overview = get_month_overview(self.user_id)

        self.stat_labels["balance"].config(
            text=f"${overview['balance']:,.2f}",
            fg=T["accent"] if overview['balance'] >= 0 else T["red"]
        )
        self.stat_labels["income"].config(text=f"${overview['income']:,.2f}")
        self.stat_labels["expenses"].config(text=f"${overview['spent']:,.2f}")
        savings = overview["savings"]
        self.stat_labels["savings"].config(
            text=f"${savings:,.2f}",
            fg=T["green"] if savings >= 0 else T["red"]
        )

        # Transactions table
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in get_recent_transactions(self.user_id, self.transaction_limit):
            date, amount, category, ttype, note = row
            tag    = "income" if ttype == "Income" else "expense"
            prefix = "+" if ttype == "Income" else "-"
            self.tree.insert("", "end",
                             values=(date, f"{prefix}${amount:.2f}", category, ttype, note),
                             tags=(tag,))

        self._update_breakdown()
        self._draw_donut()

    def _update_breakdown(self):
        for item in self.breakdown_tree.get_children():
            self.breakdown_tree.delete(item)

        summary = get_category_summary(self.user_id)
        total   = sum(a for _, a in summary)

        if not summary or total == 0:
            self.breakdown_tree.insert("", "end", values=("No data", "$0.00", "—"))
            return

        for category, amount in summary:
            pct = (amount / total * 100) if total > 0 else 0
            self.breakdown_tree.insert("", "end",
                                        values=(category, f"${amount:.2f}", f"{pct:.1f}%"))

    def _draw_donut(self):
        for w in self.donut_holder.winfo_children():
            w.destroy()

        overview = get_month_overview(self.user_id)
        spent  = max(overview["spent"],  0)
        budget = max(overview["budget"], 0)
        left   = max(budget - spent,     0)
        pct    = min(spent / budget * 100, 100) if budget > 0 else 0

        color = (T["green"] if pct < 70
                 else T["yellow"] if pct < 90
                 else T["red"])

        data   = [left, spent] if spent > 0 else [1]
        colors = [T["border"], color] if spent > 0 else [T["border"]]
        # Swap so "spent" wedge is the coloured portion
        data_plot   = [spent, left]   if spent > 0 else [1]
        colors_plot = [color, T["card2"]] if spent > 0 else [T["card2"]]

        fig = Figure(figsize=(2.8, 2.1), dpi=95)
        fig.patch.set_facecolor(T["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(T["card"])

        ax.pie(data_plot, colors=colors_plot, startangle=90,
               wedgeprops=dict(width=0.32, edgecolor=T["card"], linewidth=2))

        ax.text(0,  0.10, f"{pct:.0f}%", ha="center", va="center",
                fontsize=15, fontweight="bold", color=color)
        ax.text(0, -0.18, f"${spent:,.0f} / ${budget:,.0f}",
                ha="center", va="center", fontsize=8, color=T["subtext"])
        ax.axis("off")
        fig.tight_layout(pad=0.1)

        canvas = FigureCanvasTkAgg(fig, master=self.donut_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x")

    # ── Actions ─────────────────────────────────────────────────────────────────
    def load_more_transactions(self):
        self.transaction_limit += 10
        self.refresh_data()

    def open_transaction(self, ttype: str):
        self.destroy()
        script = os.path.join(ROOT_DIR, "Transaction.py")
        subprocess.Popen([sys.executable, script, ttype, str(self.user_id)])

    def view_history(self):
        self.destroy()
        script = os.path.join(ROOT_DIR, "Transaction.py")
        subprocess.Popen([sys.executable, script, "Income", str(self.user_id)])

    def show_reports(self):
        self.destroy()
        script = os.path.join(ROOT_DIR, "Pages", "Reports.py")
        subprocess.Popen([sys.executable, script, str(self.user_id)])

    def logout(self):
        self.destroy()
        script = os.path.join(ROOT_DIR, "Pages", "Login.py")
        subprocess.Popen([sys.executable, script])

    # ── Budget Manager (modal popup) ──────────────────────────────────────────
    def show_budgets(self):
        if self.user_id is None:
            messagebox.showinfo("Budget", "Please log in to manage your budget.")
            return

        popup = tk.Toplevel(self)
        popup.title("Budget Manager")
        popup.resizable(False, False)
        popup.configure(bg=T["bg"])
        popup.grab_set()  # modal

        # Centre popup relative to dashboard
        self.update_idletasks()
        pw, ph = 420, 400
        px = self.winfo_x() + (self.winfo_width()  - pw) // 2
        py = self.winfo_y() + (self.winfo_height() - ph) // 2
        popup.geometry(f"{pw}x{ph}+{px}+{py}")

        budget = get_user_budget(self.user_id)
        spent  = get_total_expenses(self.user_id)
        pct    = min(spent / budget * 100, 100) if budget > 0 else 0
        color  = (T["green"] if pct < 70
                  else T["yellow"] if pct < 90
                  else T["red"])

        # Title
        tk.Label(popup, text="💰  Budget Manager",
                 font=(FF, 14, "bold"), bg=T["bg"], fg=T["text"]
                 ).pack(pady=(24, 6))

        # Card
        card = tk.Frame(popup, bg=T["card"], padx=26, pady=20)
        card.pack(padx=22, fill="x")

        # Stats row
        stats = tk.Frame(card, bg=T["card"])
        stats.pack(fill="x", pady=(0, 14))

        for col, (label, value, fg) in enumerate([
            ("Monthly Budget", f"${budget:,.2f}", T["text"]),
            ("Spent This Month", f"${spent:,.2f}", color),
            ("Remaining",        f"${max(budget - spent, 0):,.2f}", T["green"] if spent <= budget else T["red"]),
        ]):
            tk.Label(stats, text=label, font=(FF, 9),
                     bg=T["card"], fg=T["subtext"]
                     ).grid(row=0, column=col, sticky="w", padx=(0, 20))
            tk.Label(stats, text=value, font=(FF, 13, "bold"),
                     bg=T["card"], fg=fg
                     ).grid(row=1, column=col, sticky="w", padx=(0, 20))

        # Progress bar
        tk.Label(card, text=f"{pct:.1f}% of budget used",
                 font=(FF, 9), bg=T["card"], fg=T["subtext"]).pack(anchor="w")

        bar_track = tk.Frame(card, bg=T["card2"], height=12)
        bar_track.pack(fill="x", pady=(5, 16))
        bar_track.pack_propagate(False)
        if pct > 0:
            fill = tk.Frame(bar_track, bg=color, height=12)
            fill.place(relwidth=min(pct / 100, 1.0), relheight=1.0)

        # New budget input
        tk.Label(card, text="Set New Monthly Budget ($)",
                 font=(FF, 10), bg=T["card"], fg=T["text"]).pack(anchor="w")

        budget_var = tk.StringVar(
            value=str(int(budget)) if budget == int(budget) else f"{budget:.2f}"
        )
        b_border = tk.Frame(card, bg=T["border"], padx=1, pady=1)
        b_entry  = tk.Entry(
            b_border, textvariable=budget_var,
            bg=T["input_bg"], fg=T["text"],
            insertbackground=T["accent"],
            relief="flat", font=(FF, 11)
        )
        b_entry.pack(fill="x", ipady=7, padx=6)
        b_border.pack(fill="x", pady=(4, 0))
        b_entry.bind("<FocusIn>",  lambda _: b_border.config(bg=T["accent"]))
        b_entry.bind("<FocusOut>", lambda _: b_border.config(bg=T["border"]))

        err_var = tk.StringVar()
        tk.Label(popup, textvariable=err_var, font=(FF, 9),
                 bg=T["bg"], fg=T["red"]).pack(pady=(8, 0))

        def save_budget():
            try:
                val = float(budget_var.get().strip())
                if val <= 0:
                    raise ValueError
                set_user_budget(self.user_id, val)
                popup.destroy()
                self.refresh_data()
            except ValueError:
                err_var.set("⚠  Please enter a valid positive number.")

        save_btn = tk.Button(
            popup, text="Save Budget", font=(FF, 11, "bold"),
            bg=T["accent"], fg="white",
            activebackground=T["accent_hover"], activeforeground="white",
            relief="flat", cursor="hand2", command=save_budget
        )
        save_btn.pack(pady=14, ipadx=28, ipady=8)
        save_btn.bind("<Enter>", lambda _: save_btn.config(bg=T["accent_hover"]))
        save_btn.bind("<Leave>", lambda _: save_btn.config(bg=T["accent"]))
        popup.bind("<Return>", lambda _: save_budget())
        b_entry.focus_set()


# ── Entry point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    app = Dashboard(user_id)
    app.mainloop()
