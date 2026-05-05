import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from core.export_excel import export_project_overview_to_excel
from core.models import StopeResult


ALL_VALUE = "All"


class ProjectOverviewTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.rows: list[dict] = []

        self.project_filter_var = tk.StringVar(value=ALL_VALUE)
        self.domain_filter_var = tk.StringVar(value=ALL_VALUE)

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        title_frame = ttk.Frame(container)
        title_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            title_frame,
            text="Calculation Log",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")

        ttk.Button(
            title_frame,
            text="Clear table",
            command=self.clear_table,
        ).pack(side="right")

        ttk.Button(
            title_frame,
            text="Export to Excel",
            command=self.export_to_excel,
        ).pack(side="right", padx=(0, 8))


        self._build_table(container)

        self.summary_var = tk.StringVar(value="No saved calculations yet.")
        ttk.Label(
            container,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(8, 0))


    def _build_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "project",
            "domain",
            "stope_id",
            "depth",
            "height",
            "avg_dip",
            "width",
            "span",
            "limiting_surface",
            "final_state",
            "comment",
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        headings = {
            "project": "Project",
            "domain": "Domain",
            "stope_id": "Stope ID",
            "depth": "Depth, m",
            "height": "Height, m",
            "avg_dip": "Avg Dip, °",
            "width": "Width, m",
            "span": "Span, m",
            "limiting_surface": "Limiting Surface",
            "final_state": "Final State",
            "comment": "Comment",
        }

        widths = {
            "project": 130,
            "domain": 120,
            "stope_id": 110,
            "depth": 80,
            "height": 80,
            "avg_dip": 90,
            "width": 80,
            "span": 80,
            "limiting_surface": 140,
            "final_state": 110,
            "comment": 260,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")

        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        horizontal_scrollbar = ttk.Scrollbar(
            parent,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        self.tree.pack(side="left", fill="both", expand=True)
        vertical_scrollbar.pack(side="right", fill="y")
        horizontal_scrollbar.pack(fill="x")

    def add_result(self, result: StopeResult, comment: str = ""):
        stope = result.stope

        row = {
            "project": stope.project_name,
            "domain": stope.domain_name,
            "stope_id": stope.stope_id,
            "depth": stope.depth_m,
            "height": stope.stope_height_m,
            "avg_dip": stope.average_dip_deg,
            "width": stope.stope_width_m,
            "span": stope.stope_span_m,
            "limiting_surface": result.limiting_surface.value,
            "final_state": result.final_state.value,
            "comment": comment,
        }

        self.rows.append(row)
        self.refresh_table()

    def _insert_row(self, row: dict):
        self.tree.insert(
            "",
            "end",
            values=(
                row["project"],
                row["domain"],
                row["stope_id"],
                f"{row['depth']:.1f}",
                f"{row['height']:.1f}",
                f"{row['avg_dip']:.1f}",
                f"{row['width']:.1f}",
                f"{row['span']:.1f}",
                row["limiting_surface"],
                row["final_state"],
                row["comment"],
            ),
        )


    def _get_filtered_rows(self) -> list[dict]:
        project_filter = self.project_filter_var.get()
        domain_filter = self.domain_filter_var.get()

        filtered = []

        for row in self.rows:
            if project_filter != ALL_VALUE and row.get("project", "") != project_filter:
                continue

            if domain_filter != ALL_VALUE and row.get("domain", "") != domain_filter:
                continue

            filtered.append(row)

        return filtered

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtered_rows = self._get_filtered_rows()

        for row in filtered_rows:
            self._insert_row(row)

        if not self.rows:
            self.summary_var.set("No saved calculations yet.")
        else:
            self.summary_var.set(
                f"Shown calculations: {len(filtered_rows)} / Total saved: {len(self.rows)}"
            )

    def apply_filters(self):
        self.refresh_table()

    def reset_filters(self):
        self.project_filter_var.set(ALL_VALUE)
        self.domain_filter_var.set(ALL_VALUE)
        self.refresh_table()

    def set_context(self, context: dict):
        project = context.get("project", "")
        domain = context.get("domain", "")

        self.project_filter_var.set(project if project else ALL_VALUE)
        self.domain_filter_var.set(domain if domain else ALL_VALUE)

        self.apply_filters()

    def clear_table(self):
        if not self.rows:
            return

        answer = messagebox.askyesno(
            "Clear Calculation Log",
            "Clear all saved calculations from Calculation Log?",
        )

        if not answer:
            return

        self.rows.clear()
        self.refresh_filter_lists()
        self.refresh_table()

    def export_to_excel(self):
        if not self.rows:
            messagebox.showinfo(
                "No data",
                "Calculation Log is empty.",
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Export Calculation Log",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile="calculation_log.xlsx",
        )

        if not output_path:
            return

        try:
            export_project_overview_to_excel(
                rows=self._get_filtered_rows(),
                output_path=output_path,
            )

            messagebox.showinfo(
                "Export complete",
                f"Calculation Log was exported to:\n{output_path}",
            )

        except Exception as error:
            messagebox.showerror("Export error", str(error))
