import tkinter as tk
from tkinter import ttk


class PlaceholderTab(ttk.Frame):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ttk.Label(
            container,
            text=title,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(
            container,
            text=message,
            justify="left",
            font=("Segoe UI", 10),
        ).pack(anchor="w")
