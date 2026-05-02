import tkinter as tk
from tkinter import ttk

from gui.calculation_tab import CalculationTab
from gui.project_overview_tab import ProjectOverviewTab
from gui.case_histories_tab import CaseHistoriesTab
from gui.stability_graph_tab import StabilityGraphTab
from gui.placeholder_tab import PlaceholderTab


class StopeForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("StopeForge")
        self.geometry("1300x850")
        self.minsize(1100, 750)

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

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

        self.export_tab = PlaceholderTab(
            notebook,
            title="Export",
            message=(
                "Export tools will be expanded in a later version.\n\n"
                "Current exports:\n"
                "- current calculation to Excel\n"
                "- project overview to Excel\n"
                "- case histories to Excel\n"
                "- stability graph to PNG"
            ),
        )

        notebook.add(self.calculation_tab, text="Calculation")
        notebook.add(self.project_overview_tab, text="Project Overview")
        notebook.add(self.case_histories_tab, text="Case Histories")
        notebook.add(self.graph_tab, text="Stability Graph")
        notebook.add(self.export_tab, text="Export")


def main():
    app = StopeForgeApp()
    app.mainloop()
