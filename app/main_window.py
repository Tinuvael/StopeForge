import tkinter as tk
from tkinter import ttk


class StopeForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("StopeForge")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        calculation_frame = ttk.Frame(notebook)
        cases_frame = ttk.Frame(notebook)
        graph_frame = ttk.Frame(notebook)
        calibration_frame = ttk.Frame(notebook)

        notebook.add(calculation_frame, text="Calculation")
        notebook.add(cases_frame, text="Case Histories")
        notebook.add(graph_frame, text="Stability Graph")
        notebook.add(calibration_frame, text="Calibration")

        ttk.Label(
            calculation_frame,
            text="Mathews–Potvin calculation module will be implemented here."
        ).pack(padx=20, pady=20, anchor="w")

        ttk.Label(
            cases_frame,
            text="Site-specific stope case history database will be implemented here."
        ).pack(padx=20, pady=20, anchor="w")

        ttk.Label(
            graph_frame,
            text="N–HR stability graph will be implemented here."
        ).pack(padx=20, pady=20, anchor="w")

        ttk.Label(
            calibration_frame,
            text="Site-specific calibration tools will be implemented here."
        ).pack(padx=20, pady=20, anchor="w")


def main():
    app = StopeForgeApp()
    app.mainloop()

