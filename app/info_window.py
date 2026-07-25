import tkinter as tk
from tkinter import ttk
from pathlib import Path

from app.config import APP_VERSION


ABOUT_TEXT = """StopeForge is a geotechnical tool for Mathews/Potvin stability assessment, case history storage, local curve calibration, and project/domain-based stope analysis.

StopeForge — геотехнический инструмент для оценки устойчивости очистных камер по методике Mathews/Potvin, хранения базы фактической отработки, калибровки локальных кривых и анализа камер по проектам и доменам.
"""


DISCLAIMER_TEXT = """Disclaimer:
This software is intended as an engineering decision-support tool. Results must be checked by a qualified geotechnical or geomechanical specialist. The software should not be used as the sole basis for final design decisions.

Дисклеймер:
Программа предназначена как инженерный инструмент поддержки принятия решений. Результаты должны проверяться квалифицированным геотехническим или геомеханическим специалистом. Программу не следует использовать как единственное основание для принятия окончательных проектных решений.
"""


def resource_path(relative_path: str) -> Path:
    """
    Works both in development and in PyInstaller bundle.
    """
    import sys

    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parents[1] / relative_path


def show_about_window(parent):
    window = tk.Toplevel(parent)
    window.title("About StopeForge")
    window.geometry("680x590")
    window.minsize(620, 520)

    content = ttk.Frame(window, padding=18)
    content.pack(fill="both", expand=True)

    # Header: logo left, app name/version right
    header = ttk.Frame(content)
    header.pack(fill="x", pady=(0, 14))

    logo_path = resource_path("assets/icons/stopeforge_icon_128x128.png")

    if logo_path.exists():
        try:
            logo_image = tk.PhotoImage(file=str(logo_path))

            logo_label = ttk.Label(header, image=logo_image)
            logo_label.image = logo_image
            logo_label.pack(side="left", padx=(0, 16))

        except tk.TclError:
            pass

    title_frame = ttk.Frame(header)
    title_frame.pack(side="left", fill="x", expand=True)

    ttk.Label(
        title_frame,
        text="StopeForge",
        font=("Segoe UI", 20, "bold"),
    ).pack(anchor="w", pady=(8, 4))

    ttk.Label(
        title_frame,
        text=f"Version: {APP_VERSION}",
        font=("Segoe UI", 10),
        foreground="#555555",
    ).pack(anchor="w")

    ttk.Label(
        content,
        text=ABOUT_TEXT,
        wraplength=590,
        justify="left",
    ).pack(anchor="w", pady=(0, 14))

    ttk.Label(
        content,
        text="Copyright © 2026 Емшанов Евгений",
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w", pady=(0, 14))

    ttk.Label(
        content,
        text=DISCLAIMER_TEXT,
        wraplength=590,
        justify="left",
        foreground="#555555",
    ).pack(anchor="w", pady=(0, 14))

    ttk.Button(
        content,
        text="Close",
        command=window.destroy,
    ).pack(anchor="e", pady=(8, 0))

    window.transient(parent)
    window.focus_set()
