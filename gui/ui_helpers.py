"""Small reusable helpers for consistent Tkinter/ttk UI spacing.

These helpers intentionally contain only presentation code. They do not touch
engineering calculations, persistence, imports/exports, or callback semantics.
"""

from __future__ import annotations

from tkinter import ttk


PAD_X = 10
PAD_Y = 8
INNER_PAD_X = 8
INNER_PAD_Y = 5
ENTRY_WIDTH = 18
COMBO_WIDTH = 18


def add_tab_header(parent: ttk.Frame, title: str, subtitle: str | None = None) -> ttk.Frame:
    """Create a compact page header and return its right-side action frame."""
    header = ttk.Frame(parent)
    header.pack(fill="x", pady=(0, PAD_Y))
    header.columnconfigure(0, weight=1)

    title_box = ttk.Frame(header)
    title_box.grid(row=0, column=0, sticky="ew")

    ttk.Label(
        title_box,
        text=title,
        font=("Segoe UI", 16, "bold"),
    ).pack(anchor="w")

    if subtitle:
        ttk.Label(
            title_box,
            text=subtitle,
            foreground="#555555",
        ).pack(anchor="w", pady=(2, 0))

    actions = ttk.Frame(header)
    actions.grid(row=0, column=1, sticky="e")
    return actions


def configure_two_column_form(frame: ttk.Frame, label_width: int = 210) -> None:
    """Apply a consistent two-column form layout."""
    frame.columnconfigure(0, minsize=label_width)
    frame.columnconfigure(1, weight=1)
