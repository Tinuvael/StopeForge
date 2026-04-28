import tkinter as tk
from tkinter import ttk

from gui.calculation_tab import CalculationTab
from gui.project_overview_tab import ProjectOverviewTab
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

        self.calculation_tab = CalculationTab(
            notebook,
            on_save_result=self.project_overview_tab.add_result,
        )

        self.case_histories_tab = PlaceholderTab(
            notebook,
            title="Case Histories",
            message=(
                "Case history database will be implemented in a later version.\n\n"
                "This tab will store observed stope performance."
            ),
        )

        self.graph_tab = PlaceholderTab(
            notebook,
            title="Stability Graph",
            message=(
                "Stability graph will be implemented in a later version.\n\n"
                "Planned graph: Mathews stability number N vs Hydraulic Radius HR."
            ),
        )

        self.export_tab = PlaceholderTab(
            notebook,
            title="Export",
            message=(
                "Export tools will be implemented in a later version.\n\n"
                "Planned exports: current calculation table, project overview, case histories, graph."
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
