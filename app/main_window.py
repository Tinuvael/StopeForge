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

        self.notebook = ttk.Notebook(paned)
        paned.add(self.notebook, weight=1)



        self.project_overview_tab = ProjectOverviewTab(self.notebook)
        self.case_histories_tab = CaseHistoriesTab(self.notebook)

        self.calculation_tab = CalculationTab(
            self.notebook,
            on_save_result=self.project_overview_tab.add_result,
            on_add_case_histories=self.case_histories_tab.add_from_current_result,
        )

        self.graph_tab = StabilityGraphTab(
            self.notebook,
            get_case_rows_callback=lambda: self.case_histories_tab.rows,
        )

        self.notebook.add(self.calculation_tab, text="Calculation")
        self.notebook.add(self.project_overview_tab, text="Calculation Log")
        self.notebook.add(self.case_histories_tab, text="Case Histories")
        self.notebook.add(self.graph_tab, text="Stability Graph")

    def on_project_context_changed(self, context):
        self.current_context = context

        active_tab = self.notebook.tab(self.notebook.select(), "text")

        if active_tab == "Calculation":
            if hasattr(self.calculation_tab, "set_context"):
                self.calculation_tab.set_context(context)

        elif active_tab == "Stability Graph":
            if hasattr(self.graph_tab, "set_context"):
                self.graph_tab.set_context(context)

        elif active_tab == "Case Histories":
            if hasattr(self.case_histories_tab, "set_context"):
                self.case_histories_tab.set_context(context)

        elif active_tab == "Calculation Log":
            if hasattr(self.project_overview_tab, "set_context"):
                self.project_overview_tab.set_context(context)


def main():
    app = StopeForgeApp()
    app.mainloop()
