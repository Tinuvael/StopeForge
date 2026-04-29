import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from core.case_store import load_cases, save_cases, DEFAULT_CASES_PATH
from core.export_excel import export_project_overview_to_excel
from core.models import SurfaceType, StopeResult


OBSERVED_STATES = [
    "Unknown",
    "Stable",
    "Unstable",
    "Caved",
]


def _safe_round(value, digits: int = 2):
    try:
        return round(float(value), digits)
    except Exception:
        return value


def _calculate_shape_factor_hr(surface_type: SurfaceType, stope) -> float:
    """
    Actual hydraulic radius / shape factor for plotting case histories.

    Crown:
        area = width * span
        perimeter = 2 * (width + span)

    Hanging wall / Footwall:
        area = height * span
        perimeter = 2 * (height + span)

    End wall:
        area = height * width
        perimeter = 2 * (height + width)
    """
    height = stope.stope_height_m
    width = stope.stope_width_m
    span = stope.stope_span_m

    if surface_type == SurfaceType.CROWN:
        a = width
        b = span
    elif surface_type in (SurfaceType.HANGING_WALL, SurfaceType.FOOTWALL):
        a = height
        b = span
    elif surface_type == SurfaceType.END_WALL:
        a = height
        b = width
    else:
        raise ValueError(f"Unknown surface type: {surface_type}")

    if a <= 0 or b <= 0:
        raise ValueError("Surface dimensions must be greater than zero.")

    return (a * b) / (2 * (a + b))


class CaseHistoriesTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.rows: list[dict] = []
        self.selected_item_id = None

        self._build_ui()
        self.load_from_database()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        title_frame = ttk.Frame(container)
        title_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            title_frame,
            text="Case Histories",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")

        ttk.Button(
            title_frame,
            text="Reload database",
            command=self.load_from_database,
        ).pack(side="right")

        ttk.Button(
            title_frame,
            text="Export to Excel",
            command=self.export_to_excel,
        ).pack(side="right", padx=(0, 8))

        ttk.Button(
            title_frame,
            text="Save database",
            command=self.save_database,
        ).pack(side="right", padx=(0, 8))

        edit_frame = ttk.LabelFrame(container, text="Edit selected case")
        edit_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(edit_frame, text="Observed state").grid(row=0, column=0, padx=6, pady=6, sticky="w")

        self.observed_state_var = tk.StringVar(value="Unknown")
        self.observed_state_combo = ttk.Combobox(
            edit_frame,
            textvariable=self.observed_state_var,
            values=OBSERVED_STATES,
            state="readonly",
            width=18,
        )
        self.observed_state_combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(edit_frame, text="Comment").grid(row=0, column=2, padx=6, pady=6, sticky="w")

        self.comment_var = tk.StringVar(value="")
        ttk.Entry(
            edit_frame,
            textvariable=self.comment_var,
            width=70,
        ).grid(row=0, column=3, padx=6, pady=6, sticky="w")

        ttk.Button(
            edit_frame,
            text="Apply to selected",
            command=self.apply_to_selected,
        ).grid(row=0, column=4, padx=6, pady=6, sticky="w")

        columns = (
            "project",
            "domain",
            "stope_id",
            "surface",
            "q_prime",
            "a",
            "b",
            "c",
            "n",
            "hr",
            "predicted_state",
            "observed_state",
            "comment",
        )

        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=20)

        headings = {
            "project": "Project",
            "domain": "Domain",
            "stope_id": "Stope ID",
            "surface": "Surface",
            "q_prime": "Q'",
            "a": "A",
            "b": "B",
            "c": "C",
            "n": "N",
            "hr": "HR",
            "predicted_state": "Predicted",
            "observed_state": "Observed",
            "comment": "Comment",
        }

        widths = {
            "project": 120,
            "domain": 120,
            "stope_id": 100,
            "surface": 120,
            "q_prime": 70,
            "a": 70,
            "b": 70,
            "c": 70,
            "n": 80,
            "hr": 80,
            "predicted_state": 110,
            "observed_state": 110,
            "comment": 300,
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

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.summary_var = tk.StringVar(value="No case histories loaded.")
        ttk.Label(
            container,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(8, 0))

    def add_from_current_result(self, result: StopeResult, default_comment: str = ""):
        new_rows = []

        for surface in result.surfaces:
            hr = _calculate_shape_factor_hr(surface.surface_type, result.stope)

            row = {
                "project": result.stope.project_name,
                "domain": result.stope.domain_name,
                "stope_id": result.stope.stope_id,
                "surface": surface.surface_type.value,
                "depth_m": result.stope.depth_m,
                "height_m": result.stope.stope_height_m,
                "avg_dip_deg": result.stope.average_dip_deg,
                "width_m": result.stope.stope_width_m,
                "span_m": result.stope.stope_span_m,
                "q_prime": _safe_round(surface.q_prime, 3),
                "a": _safe_round(surface.stress_factor_a, 3),
                "b": _safe_round(surface.joint_factor_b, 3),
                "c": _safe_round(surface.surface_factor_c, 3),
                "n": _safe_round(surface.stability_number_n, 3),
                "shape_factor_hr_m": _safe_round(hr, 3),
                "stable_hr_limit_m": _safe_round(surface.hr_stable, 3),
                "predicted_state": surface.stability_state.value,
                "observed_state": "Unknown",
                "comment": default_comment,
            }

            new_rows.append(row)

        self.rows.extend(new_rows)
        self.refresh_table()
        self.save_database()

        messagebox.showinfo(
            "Saved",
            "Current calculation was added to Case Histories.\n\n"
            "Observed state is set to Unknown. Select rows and update it manually.",
        )

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.get("project", ""),
                    row.get("domain", ""),
                    row.get("stope_id", ""),
                    row.get("surface", ""),
                    row.get("q_prime", ""),
                    row.get("a", ""),
                    row.get("b", ""),
                    row.get("c", ""),
                    row.get("n", ""),
                    row.get("shape_factor_hr_m", ""),
                    row.get("predicted_state", ""),
                    row.get("observed_state", "Unknown"),
                    row.get("comment", ""),
                ),
            )

        self.summary_var.set(
            f"Case histories: {len(self.rows)} | Database: {DEFAULT_CASES_PATH}"
        )

    def on_select(self, _event=None):
        selection = self.tree.selection()

        if not selection:
            self.selected_item_id = None
            return

        self.selected_item_id = selection[0]
        row_index = self.tree.index(self.selected_item_id)

        if row_index < 0 or row_index >= len(self.rows):
            return

        row = self.rows[row_index]

        self.observed_state_var.set(row.get("observed_state", "Unknown"))
        self.comment_var.set(row.get("comment", ""))

    def apply_to_selected(self):
        selection = self.tree.selection()

        if not selection:
            messagebox.showinfo("No selection", "Select one or more case rows first.")
            return

        observed_state = self.observed_state_var.get()
        comment = self.comment_var.get().strip()

        for item_id in selection:
            row_index = self.tree.index(item_id)

            if 0 <= row_index < len(self.rows):
                self.rows[row_index]["observed_state"] = observed_state
                self.rows[row_index]["comment"] = comment

        self.refresh_table()
        self.save_database()

    def load_from_database(self):
        self.rows = load_cases(DEFAULT_CASES_PATH)
        self.refresh_table()

    def save_database(self):
        save_cases(self.rows, DEFAULT_CASES_PATH)
        self.summary_var.set(
            f"Case histories: {len(self.rows)} | Saved to: {DEFAULT_CASES_PATH}"
        )

    def export_to_excel(self):
        if not self.rows:
            messagebox.showinfo("No data", "Case Histories table is empty.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Export Case Histories",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile="case_histories.xlsx",
        )

        if not output_path:
            return

        # Reuse simple table exporter for now.
        export_rows = []

        for row in self.rows:
            export_rows.append(
                {
                    "project": row.get("project", ""),
                    "domain": row.get("domain", ""),
                    "stope_id": row.get("stope_id", ""),
                    "depth": row.get("depth_m", ""),
                    "height": row.get("height_m", ""),
                    "avg_dip": row.get("avg_dip_deg", ""),
                    "width": row.get("width_m", ""),
                    "span": row.get("span_m", ""),
                    "limiting_surface": row.get("surface", ""),
                    "final_state": row.get("observed_state", ""),
                    "comment": row.get("comment", ""),
                }
            )

        try:
            export_project_overview_to_excel(export_rows, output_path)

            messagebox.showinfo(
                "Export complete",
                f"Case histories were exported to:\n{output_path}",
            )
        except Exception as error:
            messagebox.showerror("Export error", str(error))
