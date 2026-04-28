import tkinter as tk
from tkinter import ttk, messagebox

from core.models import StopeResult


class ProjectOverviewTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.rows: list[dict] = []

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        title_frame = ttk.Frame(container)
        title_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            title_frame,
            text="Project Overview",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")

        ttk.Button(
            title_frame,
            text="Clear table",
            command=self.clear_table,
        ).pack(side="right")

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

        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=18)

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

        vertical_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        horizontal_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        self.tree.pack(side="left", fill="both", expand=True)
        vertical_scrollbar.pack(side="right", fill="y")
        horizontal_scrollbar.pack(side="bottom", fill="x")

        self.summary_var = tk.StringVar(value="No saved calculations yet.")
        ttk.Label(
            container,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(8, 0))

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

        self.summary_var.set(f"Saved calculations: {len(self.rows)}")

    def clear_table(self):
        if not self.rows:
            return

        answer = messagebox.askyesno(
            "Clear Project Overview",
            "Clear all saved calculations from Project Overview?",
        )

        if not answer:
            return

        self.rows.clear()

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.summary_var.set("No saved calculations yet.")
