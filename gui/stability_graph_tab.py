import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from db.connection import DEFAULT_PROJECT_DB_PATH
from db.schema import initialize_database
from db.boundary_repository import (
    list_boundaries,
    list_boundaries_exact,
    find_active_boundary_exact,
    upsert_boundary,
    delete_boundary,
    set_active_boundary,
    deactivate_boundary,
)



ALL_VALUE = "All"


STATE_STYLES = {
    "Stable": {
        "color": "#2ca02c",
        "marker": "o",
        "label": "Stable",
    },
    "Unstable": {
        "color": "#ff7f0e",
        "marker": "^",
        "label": "Unstable",
    },
    "Caved": {
        "color": "#d62728",
        "marker": "s",
        "label": "Caved",
    },
    "Unknown": {
        "color": "#7f7f7f",
        "marker": "x",
        "label": "Unknown",
    },
}


LOCAL_BOUNDARY_PRESETS = {
    "Manual": None,
    "Mayskoe RZ-1": {
        "name": "Mayskoe RZ-1 boundary",
        "slope": 0.5093,
        "intercept": -0.8149,
    },
    "Mayskoe RZ-2": {
        "name": "Mayskoe RZ-2 boundary",
        "slope": 0.7787,
        "intercept": -1.2857,
    },
    "Mayskoe RZ-4": {
        "name": "Mayskoe RZ-4 boundary",
        "slope": 1.3736,
        "intercept": -1.9981,
    },
}


def _safe_float(value):
    try:
        if value is None:
            return None

        text = str(value).strip().replace(",", ".")

        if text == "":
            return None

        return float(text)

    except Exception:
        return None

def _sigmoid(value):
    value = np.clip(value, -60, 60)
    return 1.0 / (1.0 + np.exp(-value))


class StabilityGraphTab(ttk.Frame):
    def __init__(self, parent, get_case_rows_callback):
        super().__init__(parent)

        self.get_case_rows_callback = get_case_rows_callback

        self.database_path = DEFAULT_PROJECT_DB_PATH
        initialize_database(self.database_path)


        self.project_filter_var = tk.StringVar(value=ALL_VALUE)
        self.domain_filter_var = tk.StringVar(value=ALL_VALUE)
        self.surface_filter_var = tk.StringVar(value=ALL_VALUE)
        self.observed_filter_var = tk.StringVar(value=ALL_VALUE)

        self.log_x_var = tk.BooleanVar(value=True)
        self.log_y_var = tk.BooleanVar(value=True)
        self.show_labels_var = tk.BooleanVar(value=False)

        self.show_boundary_var = tk.BooleanVar(value=False)
        self.boundary_preset_var = tk.StringVar(value="Manual")
        self.boundary_name_var = tk.StringVar(value="Local boundary")
        self.boundary_slope_var = tk.StringVar(value="1.0")
        self.boundary_intercept_var = tk.StringVar(value="0.0")
        self.boundary_mode_var = tk.StringVar(value="linear")
        self.boundary_equation_var = tk.StringVar(value="Equation: N = a × HR + b")

        self.envelope_margin_var =  tk.StringVar(value="10")
        self.saved_boundary_var = tk.StringVar(value="")
        self.boundary_comment_var = tk.StringVar(value="")
        self.saved_boundaries: list[dict] = []
        self.envelope_percentile_var = tk.StringVar(value="85")
        self.visible_stats_var = tk.StringVar(value="Visible cases: no data")

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_title_bar(container)
        self._build_filters(container)
        self._build_local_boundary_controls(container)
        self._build_graph(container)
        self.refresh_filters()
        self.refresh_saved_boundaries()
        self.refresh_graph()


    def _build_title_bar(self, parent):
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            title_frame,
            text="Stability Graph",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")

        ttk.Button(
            title_frame,
            text="Export PNG",
            command=self.export_png,
        ).pack(side="right")

        ttk.Button(
            title_frame,
            text="Refresh graph",
            command=self.refresh_graph,
        ).pack(side="right", padx=(0, 8))

    def _build_filters(self, parent):
        filter_frame = ttk.LabelFrame(parent, text="Graph filters")
        filter_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(filter_frame, text="Project").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.project_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.project_filter_var,
            state="readonly",
            width=22,
        )
        self.project_filter_combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(filter_frame, text="Domain").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.domain_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.domain_filter_var,
            state="readonly",
            width=22,
        )
        self.domain_filter_combo.grid(row=0, column=3, padx=6, pady=6, sticky="w")

        ttk.Label(filter_frame, text="Surface").grid(row=0, column=4, padx=6, pady=6, sticky="w")
        self.surface_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.surface_filter_var,
            state="readonly",
            width=18,
        )
        self.surface_filter_combo.grid(row=0, column=5, padx=6, pady=6, sticky="w")

        ttk.Label(filter_frame, text="Observed").grid(row=0, column=6, padx=6, pady=6, sticky="w")
        self.observed_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.observed_filter_var,
            state="readonly",
            width=18,
        )
        self.observed_filter_combo.grid(row=0, column=7, padx=6, pady=6, sticky="w")

        ttk.Button(
            filter_frame,
            text="Apply",
            command=self.refresh_graph,
        ).grid(row=0, column=8, padx=6, pady=6)

        ttk.Button(
            filter_frame,
            text="Reset",
            command=self.reset_filters,
        ).grid(row=0, column=9, padx=6, pady=6)

        ttk.Checkbutton(
            filter_frame,
            text="Log X",
            variable=self.log_x_var,
            command=self.refresh_graph,
        ).grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ttk.Checkbutton(
            filter_frame,
            text="Log Y",
            variable=self.log_y_var,
            command=self.refresh_graph,
        ).grid(row=1, column=2, padx=6, pady=6, sticky="w")

        ttk.Checkbutton(
            filter_frame,
            text="Show stope labels",
            variable=self.show_labels_var,
            command=self.refresh_graph,
        ).grid(row=1, column=3, padx=6, pady=6, sticky="w")

        ttk.Button(
            filter_frame,
            text="Refresh filter lists",
            command=self.refresh_filter_lists,
        ).grid(row=1, column=8, padx=6, pady=6)

        for combo in (
            self.project_filter_combo,
            self.domain_filter_combo,
            self.surface_filter_combo,
            self.observed_filter_combo,
        ):
            combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_graph())

    def _build_local_boundary_controls(self, parent):
        boundary_frame = ttk.LabelFrame(parent, text="Local Boundary / Calibration")
        boundary_frame.pack(fill="x", pady=(0, 8))

        ttk.Checkbutton(
            boundary_frame,
            text="Show boundary",
            variable=self.show_boundary_var,
            command=self.refresh_graph,
        ).grid(row=0, column=0, padx=6, pady=6, sticky="w")

        ttk.Label(boundary_frame, text="Curve type").grid(
            row=0, column=1, padx=6, pady=6, sticky="w"
        )

        self.boundary_mode_combo = ttk.Combobox(
            boundary_frame,
            textvariable=self.boundary_mode_var,
            values=["linear", "power"],
            state="readonly",
            width=10,
        )
        self.boundary_mode_combo.grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.boundary_mode_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.refresh_equation_label(),
        )

        ttk.Label(boundary_frame, text="Name").grid(
            row=0, column=3, padx=6, pady=6, sticky="w"
        )
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_name_var,
            width=26,
        ).grid(row=0, column=4, padx=6, pady=6, sticky="w")

        ttk.Label(boundary_frame, text="a / slope").grid(
            row=0, column=5, padx=6, pady=6, sticky="w"
        )
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_slope_var,
            width=10,
        ).grid(row=0, column=6, padx=6, pady=6, sticky="w")

        ttk.Label(boundary_frame, text="b / intercept").grid(
            row=0, column=7, padx=6, pady=6, sticky="w"
        )
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_intercept_var,
            width=10,
        ).grid(row=0, column=8, padx=6, pady=6, sticky="w")

        ttk.Button(
            boundary_frame,
            text="Apply boundary",
            command=self.apply_manual_boundary,
        ).grid(row=0, column=9, padx=6, pady=6)

        ttk.Label(
            boundary_frame,
            textvariable=self.boundary_equation_var,
            foreground="#555555",
        ).grid(row=1, column=0, columnspan=5, padx=6, pady=(0, 6), sticky="w")




        ttk.Label(boundary_frame, text="Name").grid(row=0, column=3, padx=6, pady=6, sticky="w")
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_name_var,
            width=26,
        ).grid(row=0, column=4, padx=6, pady=6, sticky="w")

        ttk.Label(boundary_frame, text="a / slope").grid(row=0, column=5, padx=6, pady=6, sticky="w")
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_slope_var,
            width=10,
        ).grid(row=0, column=6, padx=6, pady=6, sticky="w")

        ttk.Label(boundary_frame, text="b / intercept").grid(row=0, column=7, padx=6, pady=6, sticky="w")
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_intercept_var,
            width=10,
        ).grid(row=0, column=8, padx=6, pady=6, sticky="w")

        ttk.Button(
            boundary_frame,
            text="Apply boundary",
            command=self.apply_manual_boundary,
        ).grid(row=0, column=9, padx=6, pady=6)


    

        self.boundary_equation_var = tk.StringVar(value="Equation: N = a × HR + b")

        ttk.Label(
            boundary_frame,
            textvariable=self.boundary_equation_var,
            foreground="#555555",
        ).grid(row=1, column=2, columnspan=4, padx=6, pady=(0, 6), sticky="w")
        

        ttk.Label(
            boundary_frame,
            textvariable=self.visible_stats_var,
            foreground="#555555",
        ).grid(row=1, column=5, columnspan=6, padx=6, pady=(0, 6), sticky="w")

        ttk.Label(
            boundary_frame,
            text="Saved boundary",
        ).grid(row=2, column=0, padx=6, pady=6, sticky="w")

        self.saved_boundary_combo = ttk.Combobox(
            boundary_frame,
            textvariable=self.saved_boundary_var,
            state="readonly",
            width=40,
        )
        self.saved_boundary_combo.grid(row=2, column=1, columnspan=3, padx=6, pady=6, sticky="w")

        ttk.Button(
            boundary_frame,
            text="Load boundary",
            command=self.load_selected_boundary,
        ).grid(row=2, column=4, padx=6, pady=6)

        ttk.Button(
            boundary_frame,
            text="Save boundary",
            command=self.save_current_boundary,
        ).grid(row=2, column=5, padx=6, pady=6)

        ttk.Button(
            boundary_frame,
            text="Delete boundary",
            command=self.delete_selected_boundary,
        ).grid(row=2, column=6, padx=6, pady=6)

        ttk.Button(
            boundary_frame,
            text="Set active",
            command=self.set_selected_boundary_active,
        ).grid(row=2, column=7, padx=6, pady=6)

        ttk.Button(
            boundary_frame,
            text="Deactivate",
            command=self.deactivate_selected_boundary,
        ).grid(row=2, column=8, padx=6, pady=6)

        ttk.Label(
            boundary_frame,
            text="Comment",
        ).grid(row=2, column=9, padx=6, pady=6, sticky="w")

        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_comment_var,
            width=35,
        ).grid(row=2, column=10, columnspan=4, padx=6, pady=6, sticky="w")


    def _build_graph(self, parent):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill="both", expand=True)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        toolbar_frame = ttk.Frame(graph_frame)
        toolbar_frame.pack(fill="x")

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.summary_var = tk.StringVar(value="")
        ttk.Label(
            parent,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(8, 0))

    def apply_boundary_preset(self):
        preset_name = self.boundary_preset_var.get()
        preset = LOCAL_BOUNDARY_PRESETS.get(preset_name)

        if preset is None:
            return

        self.boundary_name_var.set(preset["name"])
        self.boundary_slope_var.set(str(preset["slope"]))
        self.boundary_intercept_var.set(str(preset["intercept"]))
        self.show_boundary_var.set(True)
        self.refresh_graph()

    def _get_all_rows(self) -> list[dict]:
        if self.get_case_rows_callback is None:
            return []

        return self.get_case_rows_callback()

    def refresh_saved_boundaries(self):
        context = self._get_exact_curve_context()

        if context is None:
            self.saved_boundaries = []
            self.saved_boundary_combo["values"] = []
            self.saved_boundary_var.set("")
            return

        project, domain, surface = context

        self.saved_boundaries = list_boundaries_exact(
            project=project,
            domain=domain,
            surface=surface,
            boundary_type="Stable-Unstable",
            db_path=self.database_path,
            active_only=False,
        )

        display_values = [
            self._make_boundary_display_name(row)
            for row in self.saved_boundaries
        ]

        self.saved_boundary_combo["values"] = display_values

        active_row = None
        for row in self.saved_boundaries:
            if int(row.get("is_active", 0) or 0) == 1:
                active_row = row
                break

        if active_row is not None:
            self.saved_boundary_var.set(self._make_boundary_display_name(active_row))
        elif display_values:
            self.saved_boundary_var.set(display_values[0])
        else:
            self.saved_boundary_var.set("")


    def get_filtered_rows(self) -> list[dict]:
        rows = self._get_all_rows()

        project_filter = self.project_filter_var.get()
        domain_filter = self.domain_filter_var.get()
        surface_filter = self.surface_filter_var.get()
        observed_filter = self.observed_filter_var.get()

        filtered = []

        for row in rows:
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

    def reset_filters(self):
        self.project_filter_var.set(ALL_VALUE)
        self.domain_filter_var.set(ALL_VALUE)
        self.surface_filter_var.set(ALL_VALUE)
        self.observed_filter_var.set(ALL_VALUE)
        self.refresh_graph()

    def refresh_graph(self, load_active_boundary: bool = True):
        self.refresh_filters()

        rows = self.get_filtered_rows()
        points = self._prepare_points(rows)
        self._update_visible_stats(points)

        self.ax.clear()

        self.ax.set_title("Mathews–Potvin Stability Graph")
        self.ax.set_xlabel("Hydraulic Radius / Shape Factor HR, m")
        self.ax.set_ylabel("Mathews Stability Number N")
        self.ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)

        if self.log_x_var.get():
            self.ax.set_xscale("log")

        if self.log_y_var.get():
            self.ax.set_yscale("log")

        plotted_states = set()

        if points:
            for state_name, style in STATE_STYLES.items():
                state_points = [point for point in points if point["observed_state"] == state_name]

                if not state_points:
                    continue

                x_values = [point["hr"] for point in state_points]
                y_values = [point["n"] for point in state_points]

                self.ax.scatter(
                    x_values,
                    y_values,
                    c=style["color"],
                    marker=style["marker"],
                    label=style["label"],
                    s=55,
                    edgecolors="black" if style["marker"] != "x" else None,
                    linewidths=0.5,
                    alpha=0.85,
                )

                plotted_states.add(state_name)

                if self.show_labels_var.get():
                    for point in state_points:
                        self.ax.annotate(
                            point["label"],
                            (point["hr"], point["n"]),
                            textcoords="offset points",
                            xytext=(4, 4),
                            fontsize=8,
                        )

        if self.show_boundary_var.get():
            self._plot_local_boundary(points)

        if points or self.show_boundary_var.get():
            self.ax.legend(loc="best")
        else:
            self.ax.text(
                0.5,
                0.5,
                "No valid case history points to plot.\nAdd cases or check filters.",
                transform=self.ax.transAxes,
                ha="center",
                va="center",
                fontsize=11,
            )

        self.figure.tight_layout()

        self.summary_var.set(
            f"Shown points: {len(points)} / Filtered rows: {len(rows)} | "
            f"States: {', '.join(sorted(plotted_states)) if plotted_states else 'None'}"
        )

        self.canvas.draw()

        self.refresh_saved_boundaries()

        if load_active_boundary:
            self.load_active_boundary_for_current_filters()



    def load_active_boundary_for_current_filters(self):
        context = self._get_exact_curve_context()

        if context is None:
            self.show_boundary_var.set(False)
            return

        project, domain, surface = context

        boundary = find_active_boundary_exact(
            project=project,
            domain=domain,
            surface=surface,
            boundary_type="Stable-Unstable",
            db_path=self.database_path,
        )

        if boundary is None:
            return

        self.boundary_name_var.set(boundary.get("boundary_name", "Local boundary"))
        self.boundary_slope_var.set(str(boundary.get("slope", "1.0")))
        self.boundary_intercept_var.set(str(boundary.get("intercept", "0.0")))
        self.boundary_mode_var.set(str(boundary.get("mode", "linear") or "linear"))
        self.refresh_equation_label()



        if boundary.get("margin", "") not in ("", None):
            self.envelope_margin_var.set(str(boundary.get("margin", "")))

        if hasattr(self, "envelope_percentile_var") and boundary.get("percentile", "") not in ("", None):
            self.envelope_percentile_var.set(str(boundary.get("percentile", "")))

        self.boundary_comment_var.set(boundary.get("comment", ""))
        self.show_boundary_var.set(True)
        self.boundary_preset_var.set("Manual")

        display_name = self._make_boundary_display_name(boundary)
        self.saved_boundary_var.set(display_name)


    def refresh_equation_label(self):
        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if mode == "power":
            self.boundary_equation_var.set(
                "Equation: N = k × HR^a | a = exponent, b/intercept = k"
            )
        else:
            self.boundary_equation_var.set(
                "Equation: N = a × HR + b"
            )


    def _plot_local_boundary(self, points: list[dict]):
        slope = _safe_float(self.boundary_slope_var.get())
        intercept = _safe_float(self.boundary_intercept_var.get())
        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if slope is None or intercept is None:
            messagebox.showerror(
                "Boundary error",
                "Boundary slope and intercept must be valid numbers.",
            )
            self.show_boundary_var.set(False)
            return

        if mode == "power" and intercept <= 0:
            messagebox.showerror(
                "Boundary error",
                "For power curve, intercept is coefficient k and must be greater than zero.",
            )
            self.show_boundary_var.set(False)
            return

        x_min, x_max = self._get_boundary_x_range(points)

        if x_min <= 0 or x_max <= 0 or x_min >= x_max:
            return

        x_values = np.linspace(x_min, x_max, 300)

        if mode == "power":
            y_values = intercept * (x_values ** slope)
            equation_label = f"N = {intercept:g}×HR^{slope:g}"
        else:
            y_values = slope * x_values + intercept
            equation_label = f"N = {slope:g}×HR + {intercept:g}"

        valid_x = []
        valid_y = []

        for x, y in zip(x_values, y_values):
            if y > 0:
                valid_x.append(x)
                valid_y.append(y)

        if not valid_x:
            return

        label = self.boundary_name_var.get().strip() or "Local boundary"

        self.ax.plot(
            valid_x,
            valid_y,
            linestyle="--",
            linewidth=2.0,
            color="black",
            label=f"{label}: {equation_label}",
        )


    def _get_boundary_x_range(self, points: list[dict]) -> tuple[float, float]:
        if points:
            hr_values = [point["hr"] for point in points if point["hr"] > 0]

            if hr_values:
                x_min = min(hr_values) * 0.8
                x_max = max(hr_values) * 1.2
                return max(x_min, 0.001), x_max

        return 0.1, 10.0

    def _prepare_points(self, rows: list[dict]) -> list[dict]:
        points = []

        for row in rows:
            hr = _safe_float(row.get("shape_factor_hr_m", ""))
            n = _safe_float(row.get("n", ""))

            if hr is None or n is None:
                continue

            if hr <= 0 or n <= 0:
                continue

            observed_state = row.get("observed_state", "Unknown") or "Unknown"

            if observed_state not in STATE_STYLES:
                observed_state = "Unknown"

            label = str(row.get("stope_id", ""))

            surface = row.get("surface", "")
            if surface:
                label = f"{label} / {surface}"

            points.append(
                {
                    "hr": hr,
                    "n": n,
                    "observed_state": observed_state,
                    "label": label,
                    "row": row,
                }
            )

        return points

    def _update_visible_stats(self, points: list[dict]):
        counts = {
            "Stable": 0,
            "Unstable": 0,
            "Caved": 0,
            "Unknown": 0,
        }

        for point in points:
            state = point.get("observed_state", "Unknown")

            if state not in counts:
                state = "Unknown"

            counts[state] += 1

        self.visible_stats_var.set(
            "Visible cases: "
            f"Stable={counts['Stable']} | "
            f"Unstable={counts['Unstable']} | "
            f"Caved={counts['Caved']} | "
            f"Unknown={counts['Unknown']}"
        )


    def fit_boundary_from_visible_points(self):
        rows = self.get_filtered_rows()
        points = self._prepare_points(rows)

        usable_points = [
            point for point in points
            if point["observed_state"] in ("Stable", "Unstable", "Caved")
        ]

        stable_count = sum(1 for point in usable_points if point["observed_state"] == "Stable")
        problem_count = sum(1 for point in usable_points if point["observed_state"] in ("Unstable", "Caved"))

        if len(usable_points) < 8:
            messagebox.showwarning(
                "Insufficient data",
                "At least 8 classified points are recommended for boundary fitting.",
            )

        if stable_count < 3 or problem_count < 3:
            messagebox.showerror(
                "Cannot fit boundary",
                "Need at least 3 Stable and 3 Unstable/Caved points in the visible filtered dataset.",
            )
            return

        try:
            slope, intercept, accuracy = self._fit_linear_boundary_logistic(usable_points)

            self.boundary_name_var.set("Fitted local boundary")
            self.boundary_slope_var.set(f"{slope:.6g}")
            self.boundary_intercept_var.set(f"{intercept:.6g}")
            self.boundary_mode_var.set("linear")
            self.refresh_equation_label()
            self.show_boundary_var.set(True)
            self.boundary_preset_var.set("Manual")
            self.envelope_margin_var = tk.StringVar(value="10")

            self.refresh_graph()

            messagebox.showinfo(
                "Boundary fitted",
                "Fitted local boundary:\n\n"
                f"N = {slope:.6g} × HR + {intercept:.6g}\n\n"
                f"Stable points: {stable_count}\n"
                f"Unstable/Caved points: {problem_count}\n"
                f"Training accuracy: {accuracy:.1f}%\n\n"
                "This is a preliminary statistical boundary. Check it visually and do not treat it as a final design criterion without engineering review.",
            )

        except Exception as error:
            messagebox.showerror("Fit error", str(error))


    def _fit_linear_boundary_logistic(self, points: list[dict]) -> tuple[float, float, float]:
        """
        Fit a simple linear boundary:

            N = a * HR + b

        using logistic regression on visible case history points.

        Stable = 1
        Unstable/Caved = 0

        The fitted classifier is:

            z = w0 + w1 * HR + w2 * N

        Boundary is z = 0:

            N = -(w0 + w1 * HR) / w2
        """
        x_values = np.array([point["hr"] for point in points], dtype=float)
        y_values = np.array([point["n"] for point in points], dtype=float)

        labels = np.array(
            [1.0 if point["observed_state"] == "Stable" else 0.0 for point in points],
            dtype=float,
        )

        # Standardize features for stable optimization.
        x_mean = float(np.mean(x_values))
        x_std = float(np.std(x_values)) or 1.0
        y_mean = float(np.mean(y_values))
        y_std = float(np.std(y_values)) or 1.0

        x_scaled = (x_values - x_mean) / x_std
        y_scaled = (y_values - y_mean) / y_std

        design_matrix = np.column_stack(
            [
                np.ones_like(x_scaled),
                x_scaled,
                y_scaled,
            ]
        )

        weights = np.zeros(3, dtype=float)
        learning_rate = 0.08
        l2 = 0.01
        iterations = 6000

        for _ in range(iterations):
            logits = design_matrix @ weights
            probabilities = _sigmoid(logits)

            gradient = design_matrix.T @ (probabilities - labels) / len(labels)

            # Do not regularize intercept.
            gradient[1:] += l2 * weights[1:]

            weights -= learning_rate * gradient

        w0, w1, w2 = weights

        if abs(w2) < 1e-9:
            raise ValueError("Fitted boundary is unstable because coefficient for N is too close to zero.")

        # Convert boundary from standardized coordinates to original HR-N coordinates.
        #
        # z = w0 + w1*((HR-x_mean)/x_std) + w2*((N-y_mean)/y_std) = 0
        #
        # N = y_mean - (y_std / w2) * (w0 + w1*(HR-x_mean)/x_std)
        # N = [-(y_std*w1)/(w2*x_std)] * HR + [y_mean - (y_std/w2)*w0 + (y_std*w1*x_mean)/(w2*x_std)]
        slope = -(y_std * w1) / (w2 * x_std)
        intercept = y_mean - (y_std / w2) * w0 + (y_std * w1 * x_mean) / (w2 * x_std)

        predicted_probabilities = _sigmoid(design_matrix @ weights)
        predictions = (predicted_probabilities >= 0.5).astype(float)
        accuracy = float(np.mean(predictions == labels) * 100.0)

        return slope, intercept, accuracy

    def fit_unsafe_upper_envelope(self):
        rows = self.get_filtered_rows()
        points = self._prepare_points(rows)

        unsafe_points = [
            point for point in points
            if point["observed_state"] in ("Unstable", "Caved")
        ]

        if len(unsafe_points) < 3:
            messagebox.showerror(
                "Cannot fit envelope",
                "Need at least 3 Unstable/Caved points in the visible filtered dataset.",
            )
            return

        margin_percent = _safe_float(self.envelope_margin_var.get())

        percentile = _safe_float(self.envelope_percentile_var.get())

        if margin_percent is None:
            messagebox.showerror(
                "Envelope error",
                "Envelope margin must be a valid number.",
            )
            return

        if margin_percent < 0:
            messagebox.showerror(
                "Envelope error",
                "Envelope margin must be greater than or equal to zero.",
            )
            return

        if percentile is None:
            messagebox.showerror(
                "Envelope error",
                "Envelope percentile must be a valid number.",
            )
            return

        if percentile <= 0 or percentile > 100:
            messagebox.showerror(
                "Envelope error",
                "Envelope percentile must be between 1 and 100.",
            )
            return

        try:
            slope, intercept, used_points_count = self._fit_unsafe_upper_envelope_linear(
        unsafe_points=unsafe_points,
        margin_percent=margin_percent,
        percentile=percentile,
)

            self.boundary_name_var.set("Unsafe upper envelope")
            self.boundary_slope_var.set(f"{slope:.6g}")
            self.boundary_intercept_var.set(f"{intercept:.6g}")
            self.boundary_mode_var.set("linear")
            self.refresh_equation_label()
            self.show_boundary_var.set(True)
            self.boundary_preset_var.set("Manual")

            self.refresh_graph()

            messagebox.showinfo(
                "Envelope fitted",
                "Unsafe upper envelope fitted:\n\n"
                f"N = {slope:.6g} × HR + {intercept:.6g}\n\n"
                f"Unstable/Caved points: {len(unsafe_points)}\n"
                f"Upper-envelope support points: {used_points_count}\n"
                f"Margin: {margin_percent:.1f}%\n\n"
                f"Percentile: {percentile:.1f}%\n"
                "This is a conservative engineering boundary. Check it visually before using it as a design criterion.",
            )

        except Exception as error:
            messagebox.showerror("Envelope fit error", str(error))


    def _fit_unsafe_upper_envelope_linear(
        self,
        unsafe_points: list[dict],
        margin_percent: float,
        percentile: float,
    ) -> tuple[float, float, int]:
        """
        Fit a practical upper envelope for unsafe cases.

        Instead of forcing the boundary above every single Unstable/Caved point,
        this uses percentile points in HR bins. This avoids one high outlier
        pushing the whole boundary too far upward.

        Boundary:
            N = a * HR + b
        """
        x_values = np.array([point["hr"] for point in unsafe_points], dtype=float)
        y_values = np.array([point["n"] for point in unsafe_points], dtype=float)

        valid_mask = (x_values > 0) & (y_values > 0)
        x_values = x_values[valid_mask]
        y_values = y_values[valid_mask]

        if len(x_values) < 3:
            raise ValueError("Need at least 3 valid unsafe points with HR > 0 and N > 0.")

        support_x, support_y = self._get_percentile_bin_points(
            x_values=x_values,
            y_values=y_values,
            percentile=percentile,
        )

        if len(support_x) < 2:
            raise ValueError("Could not build enough envelope support points.")

        slope, intercept = np.polyfit(support_x, support_y, 1)

        # Apply engineering margin directly to envelope support points.
        # This makes margin behavior clear and visible:
        # margin = 10 means N_boundary is raised by 10%.
        margin_multiplier = 1.0 + margin_percent / 100.0
        support_y = support_y * margin_multiplier

        slope, intercept = np.polyfit(support_x, support_y, 1)

        return float(slope), float(intercept), len(support_x)



    def _get_percentile_bin_points(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray,
        percentile: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Build envelope support points.

        For each HR bin, take the selected percentile of N instead of maximum N.
        This is more stable than a strict upper envelope.
        """
        point_count = len(x_values)

        if point_count < 6:
            return x_values, y_values

        bin_count = min(6, max(3, int(np.sqrt(point_count))))

        x_min = float(np.min(x_values))
        x_max = float(np.max(x_values))

        if x_min == x_max:
            return x_values, y_values

        bins = np.linspace(x_min, x_max, bin_count + 1)

        support_x = []
        support_y = []

        for i in range(bin_count):
            left = bins[i]
            right = bins[i + 1]

            if i == bin_count - 1:
                mask = (x_values >= left) & (x_values <= right)
            else:
                mask = (x_values >= left) & (x_values < right)

            if not np.any(mask):
                continue

            bin_x = x_values[mask]
            bin_y = y_values[mask]

            selected_y = float(np.percentile(bin_y, percentile))

            # X берём как медиану HR в бине, чтобы линия не прыгала по крайним точкам.
            selected_x = float(np.median(bin_x))

            support_x.append(selected_x)
            support_y.append(selected_y)

        return np.array(support_x, dtype=float), np.array(support_y, dtype=float)

    def _get_current_filter_value(self, var: tk.StringVar) -> str:
        value = var.get().strip()
        return "" if value == ALL_VALUE else value


    def _make_boundary_display_name(self, row: dict) -> str:
        active = "ACTIVE" if int(row.get("is_active", 0) or 0) == 1 else "inactive"
        boundary_type = row.get("boundary_type", "") or "Stable-Unstable"
        mode = row.get("mode", "") or "linear"
        name = row.get("boundary_name", "") or "Unnamed boundary"
        slope = row.get("slope", "")
        intercept = row.get("intercept", "")

        if str(mode).lower() == "power":
            formula = f"k={intercept} a={slope}"
        else:
            formula = f"a={slope} b={intercept}"

        return f"{active} | {boundary_type} | {mode} | {name} | {formula}"



    def _get_selected_boundary_row(self) -> dict | None:
        selected_display_name = self.saved_boundary_var.get()

        if not selected_display_name:
            return None

        for row in self.saved_boundaries:
            if self._make_boundary_display_name(row) == selected_display_name:
                return row

        return None



    def save_current_boundary(self):
        slope = _safe_float(self.boundary_slope_var.get())
        intercept = _safe_float(self.boundary_intercept_var.get())
        context = self._get_exact_curve_context()

        if context is None:
            messagebox.showerror(
                "Save boundary error",
                "Select exact Project, Domain and Surface before saving a local curve.",
            )
            return

        project, domain, surface = context



        percentile = (
            _safe_float(self.envelope_percentile_var.get())
            if hasattr(self, "envelope_percentile_var")
            else None
        )

        margin = _safe_float(self.envelope_margin_var.get())

        if slope is None or intercept is None:
            messagebox.showerror(
                "Save boundary error",
                "Boundary slope and intercept must be valid numbers.",
            )
            return

        boundary_name = self.boundary_name_var.get().strip()

        if not boundary_name:
            messagebox.showerror(
                "Save boundary error",
                "Boundary name cannot be empty.",
            )
            return

        row = {
            "project": project,
            "domain": domain,
            "surface": surface,
            "boundary_name": boundary_name,
            "boundary_type": "Stable-Unstable",
            "mode": self.boundary_mode_var.get().strip().lower() or "linear",
            "slope": slope,
            "intercept": intercept,
            "percentile": percentile,
            "margin": margin,
            "is_standard": 0,
            "is_active": 1,
            "comment": self.boundary_comment_var.get().strip(),
        }

        boundary_id = upsert_boundary(row, self.database_path)
        set_active_boundary(boundary_id, self.database_path)
        self.refresh_saved_boundaries()

        display_name = self._make_boundary_display_name(row)
        self.saved_boundary_var.set(display_name)

        messagebox.showinfo(
            "Boundary saved",
            f"Boundary was saved to SQLite database:\n{self.database_path}",
        )



    def load_selected_boundary(self):
        row = self._get_selected_boundary_row()

        if row is None:
            messagebox.showinfo(
                "No boundary selected",
                "Select a saved boundary first.",
            )
            return

        project = row.get("project", "")
        domain = row.get("domain", "")
        surface = row.get("surface", "")

        self.project_filter_var.set(project if project else ALL_VALUE)
        self.domain_filter_var.set(domain if domain else ALL_VALUE)
        self.surface_filter_var.set(surface if surface else ALL_VALUE)

        self.boundary_name_var.set(row.get("boundary_name", "Local boundary"))
        self.boundary_slope_var.set(str(row.get("slope", "1.0")))
        self.boundary_intercept_var.set(str(row.get("intercept", "0.0")))

        if row.get("margin", "") not in ("", None):
            self.envelope_margin_var.set(str(row.get("margin", "")))

        if hasattr(self, "envelope_percentile_var") and row.get("percentile", "") not in ("", None):
            self.envelope_percentile_var.set(str(row.get("percentile", "")))

        self.boundary_comment_var.set(row.get("comment", ""))
        self.boundary_preset_var.set("Manual")
        self.show_boundary_var.set(True)

        self.refresh_filters()
        self.refresh_graph()


    def delete_selected_boundary(self):
        row = self._get_selected_boundary_row()

        if row is None:
            messagebox.showinfo(
                "No boundary selected",
                "Select a saved boundary first.",
            )
            return

        boundary_id = row.get("id")

        if boundary_id is None:
            messagebox.showerror(
                "Delete boundary error",
                "Selected boundary has no SQLite id.",
            )
            return

        answer = messagebox.askyesno(
            "Delete boundary",
            f"Delete saved boundary?\n\n{self._make_boundary_display_name(row)}",
        )

        if not answer:
            return

        delete_boundary(int(boundary_id), self.database_path)
        self.refresh_saved_boundaries()

        messagebox.showinfo(
            "Boundary deleted",
            "Saved boundary was deleted from SQLite database.",
        )



    def export_png(self):
        rows = self.get_filtered_rows()
        points = self._prepare_points(rows)

        if not points and not self.show_boundary_var.get():
            messagebox.showinfo(
                "No graph",
                "There are no valid points to export.",
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Export Stability Graph",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            initialfile="stability_graph.png",
        )

        if not output_path:
            return

        try:
            self.figure.savefig(output_path, dpi=300, bbox_inches="tight")

            messagebox.showinfo(
                "Export complete",
                f"Graph was exported to:\n{output_path}",
            )

        except Exception as error:
            messagebox.showerror("Export error", str(error))


    def _has_exact_curve_context(self) -> bool:
        return (
            self.project_filter_var.get().strip() != ALL_VALUE
            and self.domain_filter_var.get().strip() != ALL_VALUE
            and self.surface_filter_var.get().strip() != ALL_VALUE
        )


    def _get_exact_curve_context(self) -> tuple[str, str, str] | None:
        if not self._has_exact_curve_context():
            return None

        return (
            self.project_filter_var.get().strip(),
            self.domain_filter_var.get().strip(),
            self.surface_filter_var.get().strip(),
        )


    def set_selected_boundary_active(self):
        row = self._get_selected_boundary_row()

        if row is None:
            messagebox.showinfo(
                "No boundary selected",
                "Select a saved boundary first.",
            )
            return

        boundary_id = row.get("id")

        if boundary_id is None:
            messagebox.showerror(
                "Set active error",
                "Selected boundary has no SQLite id.",
            )
            return

        set_active_boundary(int(boundary_id), self.database_path)
        self.refresh_saved_boundaries()
        self.load_selected_boundary()
        self.refresh_graph()

        messagebox.showinfo(
            "Boundary activated",
            "Selected boundary is now active for this Project / Domain / Surface.",
        )


    def deactivate_selected_boundary(self):
        row = self._get_selected_boundary_row()

        if row is None:
            messagebox.showinfo(
                "No boundary selected",
                "Select a saved boundary first.",
            )
            return

        boundary_id = row.get("id")

        if boundary_id is None:
            messagebox.showerror(
                "Deactivate error",
                "Selected boundary has no SQLite id.",
            )
            return

        deactivate_boundary(int(boundary_id), self.database_path)
        self.refresh_saved_boundaries()
        self.refresh_graph()

        messagebox.showinfo(
            "Boundary deactivated",
            "Selected boundary was deactivated.",
        )


    def refresh_filter_lists(self):
        rows = self._get_all_rows()

        projects = sorted(
            {
                row.get("project", "")
                for row in rows
                if row.get("project", "")
            }
        )

        domains = sorted(
            {
                row.get("domain", "")
                for row in rows
                if row.get("domain", "")
            }
        )

        surfaces = sorted(
            {
                row.get("surface", "")
                for row in rows
                if row.get("surface", "")
            }
        )

        observed_states = sorted(
            {
                row.get("observed_state", "Unknown") or "Unknown"
                for row in rows
            }
        )

        self.project_filter_combo["values"] = [ALL_VALUE] + projects
        self.domain_filter_combo["values"] = [ALL_VALUE] + domains
        self.surface_filter_combo["values"] = [ALL_VALUE] + surfaces
        self.observed_filter_combo["values"] = [ALL_VALUE] + observed_states

        if self.project_filter_var.get() not in self.project_filter_combo["values"]:
            self.project_filter_var.set(ALL_VALUE)

        if self.domain_filter_var.get() not in self.domain_filter_combo["values"]:
            self.domain_filter_var.set(ALL_VALUE)

        if self.surface_filter_var.get() not in self.surface_filter_combo["values"]:
            self.surface_filter_var.set(ALL_VALUE)

        if self.observed_filter_var.get() not in self.observed_filter_combo["values"]:
            self.observed_filter_var.set(ALL_VALUE)

        self.refresh_saved_boundaries()


    def refresh_filters(self):
        self.refresh_filter_lists()

    def apply_manual_boundary(self):
        slope = _safe_float(self.boundary_slope_var.get())
        intercept = _safe_float(self.boundary_intercept_var.get())
        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if slope is None or intercept is None:
            messagebox.showerror(
                "Boundary error",
                "Boundary slope and intercept must be valid numbers.",
            )
            return

        if mode == "power" and intercept <= 0:
            messagebox.showerror(
                "Boundary error",
                "For power curve, b/intercept is coefficient k and must be greater than zero.",
            )
            return

        self.show_boundary_var.set(True)
        self.refresh_equation_label()
        self.refresh_graph(load_active_boundary=False)


