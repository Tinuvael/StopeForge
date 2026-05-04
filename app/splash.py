import sys
import tkinter as tk
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """
    Путь к ресурсам при обычном запуске и после сборки PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    # splash.py лежит в app/, поэтому parent.parent = корень проекта
    return Path(__file__).resolve().parent.parent / relative_path


def run_with_splash(
    app_factory,
    image_path: str = "assets/icons/stopeforge_icon_512x512.png",
    duration_ms: int = 1200,
    fade_ms: int = 400,
):
    """
    Сначала показывает splash screen.
    Потом закрывает его и запускает основное приложение.
    """

    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#0d1826")

    try:
        splash.attributes("-topmost", True)
        splash.attributes("-alpha", 1.0)
    except tk.TclError:
        pass

    img_path = resource_path(image_path)

    if not img_path.exists():
        print(f"[SPLASH] Image not found: {img_path}")
        splash.destroy()
        app = app_factory()
        app.mainloop()
        return

    try:
        logo = tk.PhotoImage(file=str(img_path))
    except tk.TclError as error:
        print(f"[SPLASH] Cannot load image: {img_path}")
        print(error)
        splash.destroy()
        app = app_factory()
        app.mainloop()
        return

    label = tk.Label(
        splash,
        image=logo,
        bg="#0d1826",
        bd=0,
        highlightthickness=0,
    )
    label.image = logo
    label.pack()

    # Важно: держим ссылку на картинку
    splash.logo = logo

    splash.update_idletasks()

    width = logo.width()
    height = logo.height()

    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()

    x = (screen_w - width) // 2
    y = (screen_h - height) // 2

    splash.geometry(f"{width}x{height}+{x}+{y}")

    def start_main_app():
        try:
            splash.destroy()
        except tk.TclError:
            pass

        app = app_factory()
        app.mainloop()

    def fade_out(step: int = 0):
        steps = 20

        if step >= steps:
            start_main_app()
            return

        alpha = 1.0 - ((step + 1) / steps)

        try:
            splash.attributes("-alpha", alpha)
        except tk.TclError:
            start_main_app()
            return

        splash.after(max(1, fade_ms // steps), lambda: fade_out(step + 1))

    splash.after(duration_ms, fade_out)
    splash.mainloop()
