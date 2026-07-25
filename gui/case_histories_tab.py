import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from core.case_import import import_case_histories_from_excel

from db.connection import DEFAULT_PROJECT_DB_PATH
from db.schema import initialize_database
from db.case_repository import (
    create_case,
    create_cases,
    list_cases,
    update_case,
    delete_case,
    delete_all_cases,
)


from core.export_excel import (
    build_export_completion_message,
    export_project_overview_to_excel,
    open_exported_file,
)
from core.models import SurfaceType, StopeResult
from gui.ui_helpers import add_tab_header


OBSERVED_STATES = [
    "Unknown",
    "Stable",
    "Unstable",
    "Caved",
]


ALL_VALUE = "All"


def _safe_round(value, digits: int = 2):
    try:
        return round(float(value), digits)
    except Exception:
        return value


def _calculate_shape_factor_hr(surface_type: SurfaceType, stope) -> float:
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

        self.database_path = Path(DEFAULT_PROJECT_DB_PATH)
        initialize_database(self.database_path)
        self.rows: list[dict] = []
        self.filtered_rows: list[dict] = []
        self.selected_item_id = None

        self.project_filter_var = tk.StringVar(value=ALL_VALUE)
        self.domain_filter_var = tk.StringVar(value=ALL_VALUE)
        self.surface_filter_var = tk.StringVar(value=ALL_VALUE)
        self.observed_filter_var = tk.StringVar(value=ALL_VALUE)

        self._build_ui()
        self.load_from_database()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_title_bar(container)
        self._build_database_bar(container)
        self._build_editor(container)
        self._build_table(container)
        self._build_summary(container)

    def _build_title_bar(self, parent):
        actions = add_tab_header(
            parent,
            "Case Histories",
            "SQLite-backed case database used by the stability graph.",
        )

        ttk.Button(
            actions,
            text="Import",
            command=self.import_from_excel,
        ).pack(side="right", padx=(0, 8))

        ttk.Button(
            actions,
            text="Export",
            command=self.export_to_excel,
        ).pack(side="right")

        ttk.Button(
            actions,
            text="Save",
            command=self.save_database,
        ).pack(side="right", padx=(0, 8))

    def _build_database_bar(self, parent):
        database_frame = ttk.LabelFrame(parent, text="SQLite project database")
        database_frame.pack(fill="x", pady=(0, 8))

        self.database_path_var = tk.StringVar(value=str(self.database_path))

        ttk.Label(database_frame, text="Current SQLite file").grid(
            row=0,
            column=0,
            padx=6,
            pady=6,
            sticky="w",
        )

        ttk.Entry(
            database_frame,
            textvariable=self.database_path_var,
            state="readonly",
            width=90,
        ).grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        ttk.Button(
            database_frame,
            text="Reload",
            command=self.load_from_database,
        ).grid(row=0, column=2, padx=6, pady=6)

        ttk.Button(
            database_frame,
            text="Clear",
            command=self.clear_all_cases,
        ).grid(row=0, column=3, padx=6, pady=6)

        database_frame.columnconfigure(1, weight=1)



    def _build_editor(self, parent):
        edit_frame = ttk.LabelFrame(parent, text="Edit selected case")
        edit_frame.pack(fill="x", pady=(0, 8))
        edit_frame.columnconfigure(3, weight=1)

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
        ).grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        ttk.Button(
            edit_frame,
            text="Apply",
            command=self.apply_to_selected,
        ).grid(row=0, column=4, padx=6, pady=6, sticky="w")

        ttk.Button(
            edit_frame,
            text="Delete",
            command=self.delete_selected,
        ).grid(row=0, column=5, padx=6, pady=6, sticky="w")

    def _build_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "project",
            "domain",
            "stope_id",
            "surface",
            "depth",
            "height",
            "avg_dip",
            "width",
            "span",
            "q_prime",
            "a",
            "b",
            "c",
            "n",
            "hr",
            "predicted_state",
            "calculation_mode",
            "standard_state",
            "local_state",
            "local_boundary_name",
            "local_boundary_n",
            "actual_hr_m",
            "observed_state",
            "comment",
        )


        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        headings = {
            "project": "Project",
            "domain": "Domain",
            "stope_id": "Stope ID",
            "surface": "Surface",
            "depth": "Depth",
            "height": "Height",
            "avg_dip": "Avg Dip",
            "width": "Width",
            "span": "Span",
            "q_prime": "Q'",
            "a": "A",
            "b": "B",
            "c": "C",
            "n": "N",
            "hr": "HR",
            "predicted_state": "Predicted",
            "calculation_mode": "Mode",
            "standard_state": "Standard",
            "local_state": "Local",
            "local_boundary_name": "Local Boundary",
            "local_boundary_n": "Boundary N",
            "actual_hr_m": "Actual HR",
            "observed_state": "Observed",
            "comment": "Comment",
        }


        widths = {
            "project": 120,
            "domain": 120,
            "stope_id": 100,
            "surface": 120,
            "depth": 70,
            "height": 70,
            "avg_dip": 75,
            "width": 70,
            "span": 70,
            "q_prime": 70,
            "a": 70,
            "b": 70,
            "c": 70,
            "n": 80,
            "hr": 80,
            "predicted_state": 110,
            "calculation_mode": 90,
            "standard_state": 100,
            "local_state": 100,
            "local_boundary_name": 180,
            "local_boundary_n": 100,
            "actual_hr_m": 90,
            "observed_state": 110,
            "comment": 260,
        }


        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")

        vertical_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        horizontal_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def _build_summary(self, parent):
        self.summary_var = tk.StringVar(value="No case histories loaded.")
        ttk.Label(
            parent,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(8, 0))

    def add_from_current_result(self, result: StopeResult, default_comment: str = ""):
        

            new_rows = []
            calculation_mode = getattr(result, "calculation_mode", "Standard")

            for surface in result.surfaces:
                actual_hr = getattr(surface, "actual_hr_m", None)

                if actual_hr is None:
                    actual_hr = _calculate_shape_factor_hr(surface.surface_type, result.stope)

                local_state = getattr(surface, "local_state", None)
                local_boundary_name = getattr(surface, "local_boundary_name", None)
                local_boundary_n = getattr(surface, "local_boundary_n", None)

                standard_state = surface.stability_state.value
                local_state_value = "" if local_state is None else local_state.value

                predicted_state = standard_state

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
                    "shape_factor_hr_m": _safe_round(actual_hr, 3),
                    "stable_hr_limit_m": _safe_round(surface.hr_stable, 3),
                    "predicted_state": predicted_state,
                    "calculation_mode": calculation_mode,
                    "standard_state": standard_state,
                    "local_state": local_state_value,
                    "local_boundary_name": "" if local_boundary_name is None else local_boundary_name,
                    "local_boundary_n": "" if local_boundary_n is None else _safe_round(local_boundary_n, 3),
                    "actual_hr_m": _safe_round(actual_hr, 3),
                    "observed_state": "Unknown",
                    "comment": default_comment,
                }

                new_rows.append(row)

            create_cases(new_rows, self.database_path)
            self.load_from_database()

            messagebox.showinfo(
                "Saved",
                "Current calculation was added to Case Histories.\n\n"
                "Observed state is set to Unknown. Select rows and update it manually.",
            )



    def get_filtered_rows(self) -> list[dict]:
        project_filter = self.project_filter_var.get()
        domain_filter = self.domain_filter_var.get()
        surface_filter = self.surface_filter_var.get()
        observed_filter = self.observed_filter_var.get()

        filtered = []

        for row in self.rows:
            if project_filter != ALL_VALUE and row.get("project", "") != project_filter:
                continue
            if domain_filter != ALL_VALUE and row.get("domain", "") != domain_filter:
                continue
            if surface_filter != ALL_VALUE and row.get("surface", "") != surface_filter:
                continue
            if observed_filter != ALL_VALUE and row.get("observed_state", "Unknown") != observed_filter:
                continue

            filtered.append(row)

        return filtered


    def refresh_table(self, rows: list[dict] | None = None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.filtered_rows = self.get_filtered_rows()

        for row in self.filtered_rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.get("project", ""),
                    row.get("domain", ""),
                    row.get("stope_id", ""),
                    row.get("surface", ""),
                    row.get("depth_m", ""),
                    row.get("height_m", ""),
                    row.get("avg_dip_deg", ""),
                    row.get("width_m", ""),
                    row.get("span_m", ""),
                    row.get("q_prime", ""),
                    row.get("a", ""),
                    row.get("b", ""),
                    row.get("c", ""),
                    row.get("n", ""),
                    row.get("shape_factor_hr_m", ""),
                    row.get("predicted_state", ""),
                    row.get("calculation_mode", ""),
                    row.get("standard_state", ""),
                    row.get("local_state", ""),
                    row.get("local_boundary_name", ""),
                    row.get("local_boundary_n", ""),
                    row.get("actual_hr_m", ""),
                    row.get("observed_state", "Unknown"),
                    row.get("comment", ""),
                ),
            )

        self.summary_var.set(
            f"Shown: {len(self.filtered_rows)} / Total: {len(self.rows)} | Database: {self.database_path}"
        )


    def on_select(self, _event=None):
        selection = self.tree.selection()

        if not selection:
            self.selected_item_id = None
            return

        self.selected_item_id = selection[0]
        row_index = self.tree.index(self.selected_item_id)

        if row_index < 0 or row_index >= len(self.filtered_rows):
            return

        row = self.filtered_rows[row_index]

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

            if 0 <= row_index < len(self.filtered_rows):
                selected_row = self.filtered_rows[row_index]
                selected_row["observed_state"] = observed_state
                selected_row["comment"] = comment

                case_id = selected_row.get("id")
                if case_id is not None:
                    update_case(
                        int(case_id),
                        {
                            "observed_state": observed_state,
                            "comment": comment,
                        },
                        self.database_path,
                    )

                

        self.load_from_database()

    def delete_selected(self):
        selection = self.tree.selection()

        if not selection:
            messagebox.showinfo("No selection", "Select one or more case rows first.")
            return

        answer = messagebox.askyesno(
            "Delete selected cases",
            "Delete selected case rows from the database?",
        )

        if not answer:
            return

        rows_to_delete = []

        for item_id in selection:
            row_index = self.tree.index(item_id)

            if 0 <= row_index < len(self.filtered_rows):
                rows_to_delete.append(self.filtered_rows[row_index])

        self.rows = [row for row in self.rows if row not in rows_to_delete]

        for row in rows_to_delete:
            case_id = row.get("id")
            if case_id is not None:
                delete_case(int(case_id), self.database_path)

        self.load_from_database()


    def load_from_database(self):
        self.rows = list_cases(self.database_path)
        self.database_path_var.set(str(self.database_path))
        self.refresh_table()


    def save_database(self):
        self.database_path_var.set(str(self.database_path))
        self.summary_var.set(
            f"Shown: {len(self.filtered_rows)} / Total: {len(self.rows)} | SQLite: {self.database_path}"
        )


    def new_database(self):
        messagebox.showinfo(
            "SQLite mode",
            "Case histories are now stored in the SQLite project database.",
        )


    def load_database_as(self):
        messagebox.showinfo(
            "SQLite mode",
            "Loading separate CSV databases is disabled in SQLite mode.",
        )


    def save_database_as(self):
        messagebox.showinfo(
            "SQLite mode",
            "Saving separate CSV databases is disabled in SQLite mode.",
        )



    def export_to_excel(self):
        rows_to_export = self.get_filtered_rows()

        if not rows_to_export:
            messagebox.showinfo("No data", "There are no case histories to export.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Export Case Histories",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile="case_histories.xlsx",
        )

        if not output_path:
            return

        export_rows = []

        for row in rows_to_export:
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

            opened, open_error = open_exported_file(output_path)
            message = build_export_completion_message(
                "Filtered case histories",
                output_path,
                opened,
                open_error,
            )

            messagebox.showinfo("Export complete", message)
        except Exception as error:
            messagebox.showerror("Export error", str(error))
    def import_from_excel(self):
        input_path = filedialog.askopenfilename(
            title="Import case histories from Excel",
            filetypes=[
                ("Excel workbook", "*.xlsx"),
                ("All files", "*.*"),
            ],
        )

        if not input_path:
            return

        try:
            imported_rows = import_case_histories_from_excel(input_path)

            if not imported_rows:
                messagebox.showinfo(
                    "No rows imported",
                    "No valid case history rows were found in the selected Excel file.",
                )
                return

            answer = messagebox.askyesno(
                "Import case histories",
                f"Import {len(imported_rows)} case history rows from Excel?",
            )

            if not answer:
                return

            create_cases(imported_rows, self.database_path)
            self.load_from_database()


            messagebox.showinfo(
                "Import complete",
                f"Imported rows: {len(imported_rows)}",
            )

        except Exception as error:
            messagebox.showerror("Import error", str(error))

    def clear_all_cases(self):
        answer = messagebox.askyesno(
            "Clear all cases",
            "Delete ALL case histories from the SQLite database?\n\n"
            "This cannot be undone.",
        )

        if not answer:
            return

        delete_all_cases(self.database_path)
        self.load_from_database()

        messagebox.showinfo(
            "Cases deleted",
            "All case histories were deleted from the SQLite database.",
        )

    def set_context(self, context: dict):
        project = context.get("project", "")
        domain = context.get("domain", "")
        surface = context.get("surface", "")

        self.project_filter_var.set(project if project else ALL_VALUE)
        self.domain_filter_var.set(domain if domain else ALL_VALUE)
        self.surface_filter_var.set(surface if surface else ALL_VALUE)

        self.refresh_table()

    def apply_filters(self):
        self.refresh_table()

