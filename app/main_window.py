import tkinter as tk
from tkinter import ttk
from pathlib import Path

from gui.calculation_tab import CalculationTab
from gui.project_overview_tab import ProjectOverviewTab
from gui.case_histories_tab import CaseHistoriesTab
from gui.stability_graph_tab import StabilityGraphTab
from gui.project_tree_panel import ProjectTreePanel


def resource_path(relative_path: str) -> Path:
    """
    Works both in development and in PyInstaller bundle.
    """
    import sys

    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parents[1] / relative_path


class StopeForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("StopeForge")
        self.geometry("1300x850")
        self.minsize(1100, 750)

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icons" / "stopeforge_icon.ico"

        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except tk.TclError:
                pass

        self.current_context = {
            "project": "",
            "domain": "",
            "surface": "",
        }

        self._build_ui()

    def _build_ui(self):
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        self.project_tree_panel = ProjectTreePanel(
            paned,
            on_context_changed=self.on_project_context_changed,
        )
        paned.add(self.project_tree_panel, weight=0)

        notebook = ttk.Notebook(paned)
        paned.add(notebook, weight=1)


        self.project_overview_tab = ProjectOverviewTab(notebook)
        self.case_histories_tab = CaseHistoriesTab(notebook)

        self.calculation_tab = CalculationTab(
            notebook,
            on_save_result=self.project_overview_tab.add_result,
            on_add_case_histories=self.case_histories_tab.add_from_current_result,
        )

        self.graph_tab = StabilityGraphTab(
            notebook,
            get_case_rows_callback=lambda: self.case_histories_tab.rows,
        )

        notebook.add(self.calculation_tab, text="Calculation")
        notebook.add(self.project_overview_tab, text="Calculation Log")
        notebook.add(self.case_histories_tab, text="Case Histories")
        notebook.add(self.graph_tab, text="Stability Graph")

    def on_project_context_changed(self, context):
        self.current_context = context


        print("Project context changed:", context)


def main():
    app = StopeForgeApp()
    app.mainloop()
