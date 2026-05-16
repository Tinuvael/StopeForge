import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from core.export_excel import (
    build_export_completion_message,
    export_current_calculation_to_excel,
    open_exported_file,
)
from db.project_repository import get_domain
from db.connection import DEFAULT_PROJECT_DB_PATH


from core.models import (
    JointSet,
    StopeInput,
    SurfaceInput,
    SurfaceType,
)
from core.stability import calculate_stope_result
from gui.stope_section_sketch import StopeSectionSketch, status_to_color


class CalculationTab(ttk.Frame):
    def __init__(self, parent, on_save_result=None, on_add_case_histories=None):
        super().__init__(parent)

        self.on_save_result = on_save_result
        self.on_add_case_histories = on_add_case_histories

        self.entries: dict[str, tk.StringVar] = {}
        self.surface_entries: dict[SurfaceType, dict[str, tk.StringVar]] = {}
        self.joint_entries: list[dict[str, tk.StringVar]] = []
        self.last_result = None
        self.last_joint_sets = []
        self.calculation_mode_var = tk.StringVar(value="Standard")

        self._build_ui()

    def _build_ui(self):
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True)

        # Fixed layout:
        # left input area ≈ 65%
        # right results area ≈ 35%
        main_container.columnconfigure(0, weight=65, uniform="calculation_columns")
        main_container.columnconfigure(1, weight=35, uniform="calculation_columns")
        main_container.rowconfigure(0, weight=1)

        # Left side: input panel
        left_container = ttk.Frame(main_container)
        left_container.grid(row=0, column=0, sticky="nsew")

        canvas = tk.Canvas(left_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=canvas.yview)

        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.columnconfigure(0, weight=1)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right side: result cards
        self.results_container = ttk.Frame(main_container)
        self.results_container.grid(row=0, column=1, sticky="nsew")

        self._build_project_frame()
        self._build_stress_frame()
        self._build_geometry_frame()
        self._build_joint_sets_frame()
        self._build_surface_frame()
        self._build_buttons()

        self._build_results_frame(self.results_container)






    def _add_entry(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        key: str,
        default: str = "",
        width: int = 18,
    ):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)

        var = tk.StringVar(value=default)
        entry = ttk.Entry(parent, textvariable=var, width=width)
        entry.grid(row=row, column=1, sticky="w", padx=6, pady=4)

        self.entries[key] = var

    def _build_project_frame(self):
        frame = ttk.LabelFrame(self.scrollable_frame, text="Selected context")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        self._add_entry(frame, 0, "Project name", "project_name", "Demo project")
        self._add_entry(frame, 1, "Domain", "domain_name", "Domain 1")
        self._add_entry(frame, 2, "Stope ID", "stope_id", "Stope 001")
        self._add_entry(frame, 3, "Comment", "comment", "")

        ttk.Label(frame, text="Assessment mode").grid(
            row=4,
            column=0,
            sticky="w",
            padx=6,
            pady=4,
        )

        ttk.Combobox(
            frame,
            textvariable=self.calculation_mode_var,
            values=["Standard", "Compare"],
            state="readonly",
            width=18,
        ).grid(row=4, column=1, sticky="w", padx=6, pady=4)


        frame.columnconfigure(0, minsize=260)
        frame.columnconfigure(1, minsize=180)


    def _build_stress_frame(self):
        frame = ttk.LabelFrame(self.scrollable_frame, text="Rock mass and stress parameters")
        frame.grid(row=1, column=0, sticky="ew", padx=10, pady=8)

        self._add_entry(frame, 0, "Mining depth, m", "depth_m", "500")
        self._add_entry(frame, 1, "Unit weight, t/m³", "unit_weight_t_m3", "2.7")
        self._add_entry(frame, 2, "UCS, MPa", "ucs_mpa", "100")
        self._add_entry(frame, 3, "Horizontal stress ratio K / λ", "horizontal_stress_ratio", "1.0")


    def _build_geometry_frame(self):
        frame = ttk.LabelFrame(self.scrollable_frame, text="Stope geometry", width=590)
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=8)


        self._add_entry(frame, 0, "Stope height, m", "stope_height_m", "40")
        self._add_entry(frame, 1, "Average stope dip, °", "average_dip_deg", "75")
        self._add_entry(frame, 2, "Stope width / ore thickness, m", "stope_width_m", "15")
        self._add_entry(frame, 3, "Stope span / strike length, m", "stope_span_m", "30")
        self._add_entry(frame, 4, "Hanging wall dip direction, °", "hanging_wall_dip_direction_deg", "90")

    def _build_joint_sets_frame(self):
        frame = ttk.LabelFrame(self.scrollable_frame, text="Discontinuity sets")
        frame.grid(row=3, column=0, sticky="ew", padx=10, pady=8)

        headers = ["Set", "Dip, °", "Dip direction, °"]
        for col, header in enumerate(headers):
            ttk.Label(frame, text=header, font=("Segoe UI", 9, "bold")).grid(
                row=0,
                column=col,
                padx=6,
                pady=4,
                sticky="w",
            )

        defaults = [
            ("Set 1", "30", "120"),
            ("Set 2", "70", "210"),
            ("Set 3", "", ""),
            ("Set 4", "", ""),
            ("Set 5", "", ""),
        ]

        for i, (name, dip, dip_dir) in enumerate(defaults, start=1):
            ttk.Label(frame, text=name).grid(row=i, column=0, padx=6, pady=3, sticky="w")

            dip_var = tk.StringVar(value=dip)
            dip_dir_var = tk.StringVar(value=dip_dir)

            ttk.Entry(frame, textvariable=dip_var, width=16).grid(
                row=i,
                column=1,
                padx=6,
                pady=3,
                sticky="w",
            )
            ttk.Entry(frame, textvariable=dip_dir_var, width=16).grid(
                row=i,
                column=2,
                padx=6,
                pady=3,
                sticky="w",
            )

            self.joint_entries.append(
                {
                    "dip": dip_var,
                    "dip_direction": dip_dir_var,
                }
            )

    def _build_surface_frame(self):
        frame = ttk.LabelFrame(self.scrollable_frame, text="Surface parameters")
        frame.grid(row=4, column=0, sticky="ew", padx=10, pady=8)

        headers = ["Surface", "Dip, °", "Q'", "A override"]
        for col, header in enumerate(headers):
            ttk.Label(frame, text=header, font=("Segoe UI", 9, "bold")).grid(
                row=0,
                column=col,
                padx=6,
                pady=4,
                sticky="w",
            )

        default_surfaces = [
            (SurfaceType.CROWN, "0", "20", ""),
            (SurfaceType.HANGING_WALL, "75", "20", ""),
            (SurfaceType.FOOTWALL, "75", "20", ""),
            (SurfaceType.END_WALL, "90", "20", ""),
        ]

        for row, (surface_type, dip, q_prime, stress_factor_a) in enumerate(default_surfaces, start=1):
            ttk.Label(frame, text=surface_type.value).grid(
                row=row,
                column=0,
                padx=6,
                pady=3,
                sticky="w",
            )

            dip_var = tk.StringVar(value=dip)
            q_prime_var = tk.StringVar(value=q_prime)
            stress_factor_a_var = tk.StringVar(value=stress_factor_a)

            ttk.Entry(frame, textvariable=dip_var, width=16).grid(
                row=row,
                column=1,
                padx=6,
                pady=3,
                sticky="w",
            )
            ttk.Entry(frame, textvariable=q_prime_var, width=16).grid(
                row=row,
                column=2,
                padx=6,
                pady=3,
                sticky="w",
            )
            ttk.Entry(frame, textvariable=stress_factor_a_var, width=16).grid(
                row=row,
                column=3,
                padx=6,
                pady=3,
                sticky="w",
            )

            self.surface_entries[surface_type] = {
                "dip": dip_var,
                "q_prime": q_prime_var,
                "stress_factor_a": stress_factor_a_var,
            }


    def _build_buttons(self):
        frame = ttk.Frame(self.scrollable_frame, width=590)
        frame.grid(row=5, column=0, sticky="ew", padx=10, pady=8)

        ttk.Button(
            frame,
            text="Calculate",
            command=self.calculate,
        ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        ttk.Button(
            frame,
            text="Save to Calculation Log",
            command=self.save_to_project_overview,
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        ttk.Button(
            frame,
            text="Add to Case Histories",
            command=self.add_to_case_histories,
        ).grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        ttk.Button(
            frame,
            text="Export to Excel",
            command=self.export_current_calculation,
        ).grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        frame.columnconfigure(0, minsize=280)
        frame.columnconfigure(1, minsize=280)


    def _build_results_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Calculation results")
        frame.pack(fill="both", expand=True, padx=10, pady=8)

        self.result_grid_vars = {}
        self.result_grid_labels = {}

        surfaces = [
            SurfaceType.HANGING_WALL,
            SurfaceType.FOOTWALL,
            SurfaceType.CROWN,
            SurfaceType.END_WALL,
        ]

        rows = [
            ("Dip, °", "dip"),
            ("Q′", "q_prime"),
            ("A", "a"),
            ("B", "b"),
            ("C", "c"),
            ("N′", "n"),
            ("Actual HR", "actual_hr"),
            ("HR stable", "hr"),
            ("HR cave", "hro"),
            ("Stable span", "stable_span"),
            ("Cave span", "cave_span"),
            ("Rating length", "rating_length"),
            ("Standard State", "standard_state"),
            ("Local State", "local_state"),
            ("Local Boundary", "local_boundary"),
            ("Boundary N", "local_boundary_n"),
        ]

        table = ttk.Frame(frame)
        table.pack(fill="both", expand=True, padx=6, pady=6)

        ttk.Label(
            table,
            text="Parameter",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, padx=6, pady=4, sticky="w")

        for col_index, surface_type in enumerate(surfaces, start=1):
            ttk.Label(
                table,
                text=surface_type.value,
                font=("Segoe UI", 9, "bold"),
            ).grid(row=0, column=col_index, padx=6, pady=4, sticky="w")

            self.result_grid_vars[surface_type] = {}
            self.result_grid_labels[surface_type] = {}

        for row_index, (label, key) in enumerate(rows, start=1):
            ttk.Label(
                table,
                text=label,
            ).grid(row=row_index, column=0, padx=6, pady=2, sticky="w")

            for col_index, surface_type in enumerate(surfaces, start=1):
                value_var = tk.StringVar(value="—")

                value_label = ttk.Label(
                    table,
                    textvariable=value_var,
                )
                value_label.grid(row=row_index, column=col_index, padx=6, pady=2, sticky="w")

                self.result_grid_vars[surface_type][key] = value_var
                self.result_grid_labels[surface_type][key] = value_label

        for col_index in range(5):
            table.columnconfigure(col_index, weight=1)

        self.summary_var = tk.StringVar(value="No calculation performed yet.")
        ttk.Label(
            frame,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=6, pady=(4, 8))

        sketch_frame = ttk.LabelFrame(frame, text="Schematic stope section")
        sketch_frame.pack(fill="both", expand=False, padx=6, pady=(0, 8))
        self.stope_section_sketch = StopeSectionSketch(sketch_frame)
        self.stope_section_sketch.pack(fill="both", expand=True, padx=6, pady=6)



    def _get_float(self, key: str) -> float:
        raw_value = self.entries[key].get().strip().replace(",", ".")

        if raw_value == "":
            raise ValueError(f"Field '{key}' is empty.")

        return float(raw_value)

    def _get_string(self, key: str) -> str:
        return self.entries[key].get().strip()

    @staticmethod
    def _parse_optional_float(raw_value: str):
        raw_value = raw_value.strip().replace(",", ".")

        if raw_value == "":
            return None

        return float(raw_value)

    @staticmethod
    def _format_length(value: float) -> str:
        if value == float("inf") or math.isinf(value):
            return "not limited"

        return f"{value:.2f}"

    def _collect_stope_input(self) -> StopeInput:
        return StopeInput(
            project_name=self._get_string("project_name"),
            domain_name=self._get_string("domain_name"),
            stope_id=self._get_string("stope_id"),
            depth_m=self._get_float("depth_m"),
            unit_weight_t_m3=self._get_float("unit_weight_t_m3"),
            ucs_mpa=self._get_float("ucs_mpa"),
            horizontal_stress_ratio=self._get_float("horizontal_stress_ratio"),
            stope_height_m=self._get_float("stope_height_m"),
            average_dip_deg=self._get_float("average_dip_deg"),
            stope_width_m=self._get_float("stope_width_m"),
            stope_span_m=self._get_float("stope_span_m"),
            hanging_wall_dip_direction_deg=self._get_float("hanging_wall_dip_direction_deg"),
        )

    def _collect_joint_sets(self) -> list[JointSet]:
        joint_sets: list[JointSet] = []

        for i, joint_entry in enumerate(self.joint_entries, start=1):
            dip = self._parse_optional_float(joint_entry["dip"].get())
            dip_direction = self._parse_optional_float(joint_entry["dip_direction"].get())

            if dip is None and dip_direction is None:
                continue

            if dip is None or dip_direction is None:
                raise ValueError(f"Joint set {i}: both dip and dip direction must be filled.")

            if not 0 <= dip <= 90:
                raise ValueError(f"Joint set {i}: dip must be between 0 and 90 degrees.")

            if not 0 <= dip_direction <= 360:
                raise ValueError(f"Joint set {i}: dip direction must be between 0 and 360 degrees.")

            joint_sets.append(
                JointSet(
                    name=f"Set {i}",
                    dip_deg=dip,
                    dip_direction_deg=dip_direction,
                )
            )

        return joint_sets

    def _collect_surface_inputs(self) -> list[SurfaceInput]:
        surfaces: list[SurfaceInput] = []

        for surface_type, fields in self.surface_entries.items():
            dip = self._parse_optional_float(fields["dip"].get())
            q_prime = self._parse_optional_float(fields["q_prime"].get())
            stress_factor_a = self._parse_optional_float(fields["stress_factor_a"].get())

            if dip is None:
                raise ValueError(f"{surface_type.value}: dip is empty.")
            if q_prime is None:
                raise ValueError(f"{surface_type.value}: Q' is empty.")

            if not 0 <= dip <= 90:
                raise ValueError(f"{surface_type.value}: dip must be between 0 and 90 degrees.")
            if q_prime <= 0:
                raise ValueError(f"{surface_type.value}: Q' must be greater than zero.")
            if stress_factor_a is not None and stress_factor_a <= 0:
                raise ValueError(f"{surface_type.value}: A override must be greater than zero.")

            surfaces.append(
                SurfaceInput(
                    surface_type=surface_type,
                    dip_deg=dip,
                    q_prime=q_prime,
                    stress_factor_a=stress_factor_a,
                )
            )

        return surfaces

    def calculate(self):
        try:
            stope = self._collect_stope_input()
            joint_sets = self._collect_joint_sets()
            surfaces = self._collect_surface_inputs()

            result = calculate_stope_result(
                stope=stope,
                surfaces=surfaces,
                joint_sets=joint_sets,
                calculation_mode=self.calculation_mode_var.get(),
            )

            self.last_result = result
            self.last_joint_sets = joint_sets
            self._show_result(result)

        except Exception as error:
            self.stope_section_sketch.draw_placeholder(
                "Cannot draw sketch: check stope geometry inputs."
            )
            messagebox.showerror("Calculation error", str(error))

    def _state_color(self, state_text: str) -> str:
        return status_to_color(state_text)

    def _set_result_value(self, surface_type: SurfaceType, key: str, value: str):
        value_var = self.result_grid_vars.get(surface_type, {}).get(key)

        if value_var is not None:
            value_var.set(value)

        label = self.result_grid_labels.get(surface_type, {}).get(key)

        if label is not None:
            if key in ("standard_state", "local_state"):
                label.configure(
                    foreground=self._state_color(value),
                    font=("Segoe UI", 9, "bold"),
                )
            else:
                label.configure(
                    foreground="#000000",
                    font=("Segoe UI", 9),
                )


    def _show_result(self, result):

        for surface_type, fields in self.result_grid_vars.items():
            for key, value_var in fields.items():
                value_var.set("—")

                label = self.result_grid_labels.get(surface_type, {}).get(key)
                if label is not None:
                    label.configure(
                        foreground="#000000",
                        font=("Segoe UI", 9),
                    )

        for surface in result.surfaces:
            surface_type = surface.surface_type

            self._set_result_value(surface_type, "dip", f"{surface.dip_deg:.1f}")
            self._set_result_value(surface_type, "q_prime", f"{surface.q_prime:.2f}")
            self._set_result_value(surface_type, "a", f"{surface.stress_factor_a:.3f}")
            self._set_result_value(surface_type, "b", f"{surface.joint_factor_b:.3f}")
            self._set_result_value(surface_type, "c", f"{surface.surface_factor_c:.3f}")
            self._set_result_value(surface_type, "n", f"{surface.stability_number_n:.2f}")

            self._set_result_value(
                surface_type,
                "actual_hr",
                "—" if surface.actual_hr_m is None else f"{surface.actual_hr_m:.2f}",
            )

            self._set_result_value(surface_type, "hr", f"{surface.hr_stable:.2f}")
            self._set_result_value(surface_type, "hro", f"{surface.hr_caving:.2f}")
            self._set_result_value(
                surface_type,
                "stable_span",
                self._format_length(surface.stable_strike_length_m),
            )
            self._set_result_value(
                surface_type,
                "cave_span",
                self._format_length(surface.cave_strike_length_m),
            )
            self._set_result_value(surface_type, "rating_length", f"{surface.rating_length_m:.2f}")

            self._set_result_value(
                surface_type,
                "standard_state",
                surface.stability_state.value,
            )

            self._set_result_value(
                surface_type,
                "local_state",
                "—" if surface.local_state is None else surface.local_state.value,
            )

            self._set_result_value(
                surface_type,
                "local_boundary",
                "—" if surface.local_boundary_name is None else surface.local_boundary_name,
            )

            self._set_result_value(
                surface_type,
                "local_boundary_n",
                "—" if surface.local_boundary_n is None else f"{surface.local_boundary_n:.2f}",
            )

        summary_text = (
            f"Mode: {result.calculation_mode} | "
            f"Standard final state: {result.final_state.value} | "
            f"Limiting surface: {result.limiting_surface.value}"
        )

        if result.local_final_state is not None:
            summary_text += f" | Local final state: {result.local_final_state.value}"

        self.summary_var.set(summary_text)
        self.stope_section_sketch.draw_result(result)



    def save_to_project_overview(self):
        if self.last_result is None:
            messagebox.showinfo(
                "No calculation",
                "Run calculation first.",
            )
            return

        if self.on_save_result is None:
            messagebox.showerror(
                "Save error",
                "Calculation Log tab is not connected.",
            )
            return

        comment = self._get_string("comment")

        self.on_save_result(self.last_result, comment)

        messagebox.showinfo(
            "Saved",
            "Calculation result was saved to Calculation Log.",
        )
    
    def export_current_calculation(self):
        if self.last_result is None:
            messagebox.showinfo(
                "No calculation",
                "Run calculation first.",
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Export current calculation",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile=f"{self.last_result.stope.stope_id}_calculation.xlsx",
        )

        if not output_path:
            return

        try:
            export_current_calculation_to_excel(
                result=self.last_result,
                joint_sets=self.last_joint_sets,
                output_path=output_path,
            )

            opened, open_error = open_exported_file(output_path)
            message = build_export_completion_message(
                "Calculation",
                output_path,
                opened,
                open_error,
            )

            messagebox.showinfo("Export complete", message)

        except Exception as error:
            messagebox.showerror("Export error", str(error))

    def add_to_case_histories(self):
        if self.last_result is None:
            messagebox.showinfo(
                "No calculation",
                "Run calculation first.",
            )
            return

        if self.on_add_case_histories is None:
            messagebox.showerror(
                "Save error",
                "Case Histories tab is not connected.",
            )
            return

        comment = self._get_string("comment")

        self.on_add_case_histories(self.last_result, comment)

    def set_context(self, context: dict):
        project = context.get("project", "")
        domain = context.get("domain", "")
        domain_id = context.get("domain_id")

        if project:
            self._set_entry("project_name", project)

        if domain:
            self._set_entry("domain_name", domain)

        if not domain_id:
            return

        domain_row = get_domain(
            int(domain_id),
            db_path=DEFAULT_PROJECT_DB_PATH,
        )

        if not domain_row:
            return

        self.apply_domain_properties(domain_row)



    def _set_entry(self, key: str, value):
        if value is None:
            return

        if value == "":
            return

        variable = self.entries.get(key)

        if variable is not None:
            variable.set(str(value))


    def _set_surface_entry(self, surface_type: SurfaceType, key: str, value):
        if value is None:
            return

        if value == "":
            return

        surface_fields = self.surface_entries.get(surface_type)

        if not surface_fields:
            return

        variable = surface_fields.get(key)

        if variable is not None:
            variable.set(str(value))


    def _set_joint_entry(self, index: int, key: str, value):
        if value is None:
            return

        if value == "":
            return

        list_index = index - 1

        if list_index < 0 or list_index >= len(self.joint_entries):
            return

        variable = self.joint_entries[list_index].get(key)

        if variable is not None:
            variable.set(str(value))


    def apply_domain_properties(self, domain_row: dict):
        # Basic rock mass and stress parameters
        self._set_entry("depth_m", domain_row.get("mining_depth_m"))
        self._set_entry("unit_weight_t_m3", domain_row.get("unit_weight_t_m3"))
        self._set_entry("ucs_mpa", domain_row.get("ucs_mpa"))
        self._set_entry("horizontal_stress_ratio", domain_row.get("horizontal_stress_ratio"))

        # Orebody parameters
        orebody_dip_direction = domain_row.get("orebody_dip_direction_deg")
        orebody_dip_angle = domain_row.get("orebody_dip_angle_deg")
        orebody_thickness = domain_row.get("orebody_thickness_m")

        # Orebody dip direction = hanging wall dip direction
        self._set_entry("hanging_wall_dip_direction_deg", orebody_dip_direction)

        # Orebody dip angle = average stope dip
        self._set_entry("average_dip_deg", orebody_dip_angle)

        # Orebody thickness = stope width / ore thickness
        self._set_entry("stope_width_m", orebody_thickness)

        # Surface dips:
        # Crown stays 0
        # Hanging wall and Footwall use orebody dip angle
        # End wall stays 90
        self._set_surface_entry(SurfaceType.HANGING_WALL, "dip", orebody_dip_angle)
        self._set_surface_entry(SurfaceType.FOOTWALL, "dip", orebody_dip_angle)

        # Q′ values:
        # If surface-specific Q′ is empty in domain settings, use Default Q′.
        q_default = domain_row.get("q_prime_default")

        q_crown = domain_row.get("q_prime_crown") or q_default
        q_hw = domain_row.get("q_prime_hanging_wall") or q_default
        q_fw = domain_row.get("q_prime_footwall") or q_default
        q_end = domain_row.get("q_prime_end_wall") or q_default

        self._set_surface_entry(SurfaceType.CROWN, "q_prime", q_crown)
        self._set_surface_entry(SurfaceType.HANGING_WALL, "q_prime", q_hw)
        self._set_surface_entry(SurfaceType.FOOTWALL, "q_prime", q_fw)
        self._set_surface_entry(SurfaceType.END_WALL, "q_prime", q_end)


        # Clear old joint sets before applying selected domain.
        # Otherwise old domain values remain when the new domain has fewer sets.
        self._clear_joint_entries()

        # Joint sets
        for index in range(1, 6):
            self._set_joint_entry(
                index,
                "dip",
                domain_row.get(f"joint{index}_dip_deg"),
            )
            self._set_joint_entry(
                index,
                "dip_direction",
                domain_row.get(f"joint{index}_dip_direction_deg"),
            )

    def _clear_joint_entries(self):
        for joint_entry in self.joint_entries:
            joint_entry["dip"].set("")
            joint_entry["dip_direction"].set("")
