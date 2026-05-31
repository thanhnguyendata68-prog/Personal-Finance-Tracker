"""
Pages/Reports.py — Financial reports with charts and summary statistics.
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os

# ── Paths & shared module ──────────────────────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from db import (THEME as T, FONT as FF,
                create_all_tables,
                get_monthly_summary, get_category_summary,
                get_total_income, get_total_expenses,
                get_all_time_balance, get_current_month)

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import ticker


class ReportsPage(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

        create_all_tables()

        self.title("Personal Finance Tracker — Reports")
        self.geometry("1100x720")
        self.resizable(False, False)
        self.configure(bg=T["bg"])
        self._center()
        self._build_ui()

    # ── Setup ──────────────────────────────────────────────────────────────────
    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1100x720+{(sw - 1100) // 2}+{(sh - 720) // 2}")

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_summary_cards()
        self._build_charts()

    def _build_header(self):
        header = tk.Frame(self, bg=T["card"], pady=13)
        header.pack(fill="x")

        tk.Label(header, text="📊  Financial Reports",
                 font=(FF, 15, "bold"), bg=T["card"], fg=T["text"]
                 ).pack(side="left", padx=20)

        back_btn = tk.Button(
            header, text="← Dashboard", font=(FF, 10),
            bg=T["card2"], fg=T["accent"],
            activebackground=T["border"], activeforeground=T["accent"],
            relief="flat", cursor="hand2",
            command=self._back_to_dashboard,
            padx=14, pady=6
        )
        back_btn.pack(side="right", padx=16)

    def _build_summary_cards(self):
        row = tk.Frame(self, bg=T["bg"])
        row.pack(fill="x", padx=18, pady=14)

        month   = get_current_month()
        income  = get_total_income(self.user_id, month)
        expense = get_total_expenses(self.user_id, month)
        balance = get_all_time_balance(self.user_id)
        savings = income - expense

        all_income  = get_total_income(self.user_id,  None)
        all_expense = get_total_expenses(self.user_id, None)

        cards = [
            ("💳  Net Balance",          f"${balance:,.2f}",  T["accent"]),
            ("📈  This Month Income",    f"${income:,.2f}",   T["green"]),
            ("📉  This Month Expenses",  f"${expense:,.2f}",  T["red"]),
            ("💵  Monthly Savings",      f"${savings:,.2f}",  T["green"] if savings >= 0 else T["red"]),
            ("📦  All-Time Income",      f"${all_income:,.2f}",  T["green"]),
            ("📦  All-Time Expenses",    f"${all_expense:,.2f}", T["red"]),
        ]

        for title, value, color in cards:
            card = tk.Frame(row, bg=T["card"], padx=14, pady=12)
            card.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(card, text=title, font=(FF, 8),
                     bg=T["card"], fg=T["subtext"]).pack(anchor="w")
            tk.Label(card, text=value, font=(FF, 14, "bold"),
                     bg=T["card"], fg=color).pack(anchor="w", pady=(4, 0))

    def _build_charts(self):
        charts = tk.Frame(self, bg=T["bg"])
        charts.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self._build_bar_chart(charts)
        self._build_pie_chart(charts)

    def _build_bar_chart(self, parent):
        """6-month Income vs Expenses grouped bar chart."""
        frame = tk.Frame(parent, bg=T["card"], padx=16, pady=14)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(frame, text="6-Month Income vs Expenses",
                 font=(FF, 12, "bold"), bg=T["card"], fg=T["text"]
                 ).pack(anchor="w", pady=(0, 8))

        data     = get_monthly_summary(self.user_id, months=6)
        labels   = [d[0] for d in data]
        incomes  = [d[1] for d in data]
        expenses = [d[2] for d in data]

        fig = Figure(figsize=(6.0, 4.0), dpi=95)
        fig.patch.set_facecolor(T["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(T["card"])

        x = list(range(len(labels)))
        w = 0.36
        bars_inc = ax.bar([i - w / 2 for i in x], incomes,  w,
                           label="Income",   color=T["green"], alpha=0.85, zorder=3)
        bars_exp = ax.bar([i + w / 2 for i in x], expenses, w,
                           label="Expenses", color=T["red"],   alpha=0.85, zorder=3)

        # Value labels on bars
        for bar in list(bars_inc) + list(bars_exp):
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 10,
                        f"${h:,.0f}", ha="center", va="bottom",
                        fontsize=7.5, color=T["subtext"])

        ax.set_xticks(x)
        ax.set_xticklabels(labels, color=T["subtext"], fontsize=10)
        ax.tick_params(axis="y", colors=T["subtext"])
        for spine in ax.spines.values():
            spine.set_edgecolor(T["border"])
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda v, _: f"${v:,.0f}")
        )
        ax.grid(axis="y", alpha=0.25, color=T["border"], zorder=0)
        ax.legend(facecolor=T["card2"], labelcolor=T["text"],
                  fontsize=9, edgecolor=T["border"])
        fig.tight_layout(pad=1.2)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_pie_chart(self, parent):
        """Category breakdown pie chart for current month."""
        frame = tk.Frame(parent, bg=T["card"], padx=16, pady=14, width=340)
        frame.pack(side="left", fill="y")
        frame.pack_propagate(False)

        tk.Label(frame, text="Expenses by Category (This Month)",
                 font=(FF, 12, "bold"), bg=T["card"], fg=T["text"]
                 ).pack(anchor="w", pady=(0, 8))

        summary = get_category_summary(self.user_id)

        fig = Figure(figsize=(3.2, 4.0), dpi=95)
        fig.patch.set_facecolor(T["card"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(T["card"])

        if not summary:
            ax.text(0.5, 0.5, "No expense data\nthis month",
                    ha="center", va="center", fontsize=12,
                    color=T["subtext"], transform=ax.transAxes)
            ax.axis("off")
        else:
            cats    = [r[0] for r in summary]
            amounts = [r[1] for r in summary]
            palette = [
                T["accent"], T["green"], T["red"],
                T["yellow"], "#3498db", "#9b59b6",
                "#1abc9c",   "#e67e22"
            ]
            wedges, texts, autotexts = ax.pie(
                amounts,
                labels=cats,
                autopct="%1.1f%%",
                colors=palette[:len(amounts)],
                startangle=90,
                textprops={"color": T["text"], "fontsize": 9},
                wedgeprops={"edgecolor": T["card"], "linewidth": 2}
            )
            for at in autotexts:
                at.set_color(T["bg"])
                at.set_fontsize(8)
                at.set_fontweight("bold")

        fig.tight_layout(pad=0.8)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # ── Category table below chart ────────────────────────────────────────
        if summary:
            tk.Label(frame, text="Category Detail", font=(FF, 10, "bold"),
                     bg=T["card"], fg=T["text"]).pack(anchor="w", pady=(10, 4))

            total = sum(a for _, a in summary)
            for cat, amt in summary:
                pct = amt / total * 100 if total > 0 else 0
                row = tk.Frame(frame, bg=T["card"])
                row.pack(fill="x", pady=1)
                tk.Label(row, text=cat, font=(FF, 9),
                         bg=T["card"], fg=T["text"], anchor="w"
                         ).pack(side="left")
                tk.Label(row, text=f"${amt:.2f}  ({pct:.1f}%)",
                         font=(FF, 9), bg=T["card"], fg=T["subtext"], anchor="e"
                         ).pack(side="right")

    # ── Navigation ─────────────────────────────────────────────────────────────
    def _back_to_dashboard(self):
        self.destroy()
        script = os.path.join(ROOT_DIR, "Dashboard.py")
        subprocess.Popen([sys.executable, script, str(self.user_id)])


# ── Entry point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python Reports.py <user_id>")
        sys.exit(1)
    uid = int(sys.argv[1])
    app = ReportsPage(uid)
    app.mainloop()
