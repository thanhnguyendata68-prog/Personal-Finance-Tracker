"""
ui_helpers.py — Shared Tkinter UI utilities for Personal Finance Tracker.
Centralises reusable widget builders so they aren't duplicated across screens.
"""

import tkinter as tk
from db import THEME as T, FONT as FF


def make_entry(parent, var=None, show=None):
    """
    Build a dark-theme Entry widget with a focus-highlight border.

    Returns
    -------
    (entry, border) : tuple
        entry  — the tk.Entry widget
        border — the tk.Frame acting as the visible border
    """
    border = tk.Frame(parent, bg=T["border"], padx=1, pady=1)
    kw = dict(
        bg=T["input_bg"], fg=T["text"],
        insertbackground=T["accent"],
        relief="flat", font=(FF, 11), bd=0
    )
    if var is not None:
        kw["textvariable"] = var
    if show is not None:
        kw["show"] = show

    entry = tk.Entry(border, **kw)
    entry.pack(fill="x", ipady=9, padx=8)
    border.pack(fill="x", pady=(0, 2))

    entry.bind("<FocusIn>",  lambda _: border.config(bg=T["accent"]))
    entry.bind("<FocusOut>", lambda _: border.config(bg=T["border"]))
    return entry, border


def center_window(win, w, h):
    """Centre a Tkinter window on the screen."""
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
