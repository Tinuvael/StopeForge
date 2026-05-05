import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from db.boundary_repository import (
    deactivate_boundary,
    delete_boundary,
    find_active_boundary_exact,
    list_boundaries_exact,
    set_active_boundary,
    upsert_boundary,
)
from db.connection import DEFAULT_PROJECT_DB_PATH
from db.schema import initialize_database


ALL_VALUE = "All"

STATE_STYLES = {
    "Stable": {"color": "#2ca02c", "marker": "o", "label": "Stable"},
    "Unstable": {"color": "#ff7f0e", "marker": "^", "label": "Unstable"},
    "Caved": {"color": "#d62728", "marker": "s", "label": "Caved"},
    "Unknown": {"color": "#7f7f7f", "marker": "x", "label": "Unknown"},
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
        self.show_inactive_curves_var = tk.BooleanVar(value=False)
        self.boundary_name_var = tk.StringVar(value="Local boundary")
        self.boundary_mode_var = tk.StringVar(value="linear")
        self.boundary_slope_var = tk.StringVar(value="1.0")
        self.boundary_intercept_var = tk.StringVar(value="0.0")
        self.boundary_equation_var = tk.StringVar(value="Equation: N = a × HR + b")
        self.point1_hr_var = tk.StringVar(value="")
        self.point1_n_var = tk.StringVar(value="")
        self.point2_hr_var = tk.StringVar(value="")
        self.point2_n_var = tk.StringVar(value="")
        self.edit_curve_points_var = tk.BooleanVar(value=False)
        self.dragged_curve_point = None
        self.curve_point_artists = []
        self.frozen_axis_limits = None
        self.boundary_comment_var = tk.StringVar(value="")
        self.saved_boundary_var = tk.StringVar(value="")
        self.saved_boundaries: list[dict] = []

        self.visible_stats_var = tk.StringVar(value="Visible cases: no data")
        self.summary_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_title_bar(container)
        self._build_filters(container)
        self._build_local_boundary_controls(container)
        self._build_graph(container)

        self.refresh_filter_lists()
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
        boundary_frame = ttk.LabelFrame(parent, text="Local Curve")
        boundary_frame.pack(fill="x", pady=(0, 8))

        ttk.Checkbutton(
            boundary_frame,
            text="Show curve",
            variable=self.show_boundary_var,
            command=lambda: self.refresh_graph(load_active_boundary=False),
        ).grid(row=0, column=0, padx=6, pady=6, sticky="w")

        ttk.Checkbutton(
            boundary_frame,
            text="Show inactive curves",
            variable=self.show_inactive_curves_var,
            command=self.refresh_graph,
        ).grid(row=3, column=11, padx=6, pady=6, sticky="w")


        ttk.Button(
            boundary_frame,
            text="Clear edit points",
            command=self.clear_edit_points,
        ).grid(row=3, column=10, padx=6, pady=6, sticky="w")


        ttk.Label(boundary_frame, text="Type").grid(row=0, column=1, padx=6, pady=6, sticky="w")
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
            lambda _event: self.apply_manual_boundary(),
        )

        ttk.Label(boundary_frame, text="Name").grid(row=0, column=3, padx=6, pady=6, sticky="w")
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_name_var,
            width=24,
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
            text="Apply curve",
            command=self.apply_manual_boundary,
        ).grid(row=0, column=9, padx=6, pady=6)

        ttk.Label(
            boundary_frame,
            textvariable=self.boundary_equation_var,
            foreground="#555555",
        ).grid(row=1, column=0, columnspan=5, padx=6, pady=(0, 6), sticky="w")


        ttk.Checkbutton(
            boundary_frame,
            text="Edit points on graph",
            variable=self.edit_curve_points_var,
            command=self.on_edit_points_toggle,
        ).grid(row=3, column=0, padx=6, pady=6, sticky="w")



        ttk.Label(
            boundary_frame,
            textvariable=self.visible_stats_var,
            foreground="#555555",
        ).grid(row=1, column=5, columnspan=5, padx=6, pady=(0, 6), sticky="w")

        ttk.Label(boundary_frame, text="Saved curve").grid(row=2, column=0, padx=6, pady=6, sticky="w")
        self.saved_boundary_combo = ttk.Combobox(
            boundary_frame,
            textvariable=self.saved_boundary_var,
            state="readonly",
            width=56,
        )
        self.saved_boundary_combo.grid(row=2, column=1, columnspan=4, padx=6, pady=6, sticky="w")

        ttk.Button(
            boundary_frame,
            text="Load",
            command=self.load_selected_boundary,
        ).grid(row=2, column=5, padx=6, pady=6)

        ttk.Button(
            boundary_frame,
            text="Save",
            command=self.save_current_boundary,
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

        ttk.Button(
            boundary_frame,
            text="Delete",
            command=self.delete_selected_boundary,
        ).grid(row=2, column=9, padx=6, pady=6)

        ttk.Label(boundary_frame, text="Comment").grid(row=4, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(
            boundary_frame,
            textvariable=self.boundary_comment_var,
            width=120,
        ).grid(row=4, column=1, columnspan=8, padx=6, pady=6, sticky="we")

    def _build_graph(self, parent):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill="both", expand=True)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.mpl_connect("button_press_event", self.on_graph_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_graph_mouse_move)
        self.canvas.mpl_connect("button_release_event", self.on_graph_mouse_release)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        toolbar_frame = ttk.Frame(graph_frame)
        toolbar_frame.pack(fill="x")

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        ttk.Label(
            parent,
            textvariable=self.summary_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(8, 0))

    def _get_all_rows(self) -> list[dict]:
        if self.get_case_rows_callback is None:
            return []
        return self.get_case_rows_callback()

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

    def refresh_filter_lists(self):
        rows = self._get_all_rows()

        projects = sorted({row.get("project", "") for row in rows if row.get("project", "")})
        domains = sorted({row.get("domain", "") for row in rows if row.get("domain", "")})
        surfaces = sorted({row.get("surface", "") for row in rows if row.get("surface", "")})
        observed_states = sorted(
            {row.get("observed_state", "Unknown") or "Unknown" for row in rows}
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

        display_values = [self._make_boundary_display_name(row) for row in self.saved_boundaries]
        self.saved_boundary_combo["values"] = display_values

        active_row = next(
            (row for row in self.saved_boundaries if int(row.get("is_active", 0) or 0) == 1),
            None,
        )

        if active_row is not None:
            self.saved_boundary_var.set(self._make_boundary_display_name(active_row))
        elif display_values:
            self.saved_boundary_var.set(display_values[0])
        else:
            self.saved_boundary_var.set("")

    def refresh_equation_label(self):
        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if mode == "power":
            self.boundary_equation_var.set(
                "Equation: N = k × HR^a | a = exponent, b/intercept = k"
            )
        else:
            self.boundary_equation_var.set("Equation: N = a × HR + b")

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

    def apply_manual_boundary(self):
        slope = _safe_float(self.boundary_slope_var.get())
        intercept = _safe_float(self.boundary_intercept_var.get())
        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if slope is None or intercept is None:
            messagebox.showerror(
                "Curve error",
                "Curve slope and intercept must be valid numbers.",
            )
            return

        if mode == "power" and intercept <= 0:
            messagebox.showerror(
                "Curve error",
                "For power curve, b/intercept is coefficient k and must be greater than zero.",
            )
            return

        self.show_boundary_var.set(True)
        self.refresh_equation_label()
        self.refresh_graph(load_active_boundary=False)


    def build_boundary_from_two_points(self):
        hr1 = _safe_float(self.point1_hr_var.get())
        n1 = _safe_float(self.point1_n_var.get())
        hr2 = _safe_float(self.point2_hr_var.get())
        n2 = _safe_float(self.point2_n_var.get())

        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if hr1 is None or n1 is None or hr2 is None or n2 is None:
            messagebox.showerror(
                "Two-point boundary error",
                "Both points must have valid HR and N values.",
            )
            return

        if hr1 <= 0 or hr2 <= 0 or n1 <= 0 or n2 <= 0:
            messagebox.showerror(
                "Two-point boundary error",
                "HR and N values must be greater than zero.",
            )
            return

        if abs(hr2 - hr1) < 1e-12:
            messagebox.showerror(
                "Two-point boundary error",
                "Point 1 HR and Point 2 HR must be different.",
            )
            return

        if mode == "power":
            if abs(np.log(hr2 / hr1)) < 1e-12:
                messagebox.showerror(
                    "Two-point boundary error",
                    "Cannot build power curve because HR ratio is too close to 1.",
                )
                return

            slope = np.log(n2 / n1) / np.log(hr2 / hr1)
            intercept = n1 / (hr1 ** slope)

            if intercept <= 0:
                messagebox.showerror(
                    "Two-point boundary error",
                    "Power coefficient k must be greater than zero.",
                )
                return

        else:
            slope = (n2 - n1) / (hr2 - hr1)
            intercept = n1 - slope * hr1

        self.boundary_slope_var.set(f"{slope:.6g}")
        self.boundary_intercept_var.set(f"{intercept:.6g}")

        if not self.boundary_name_var.get().strip() or self.boundary_name_var.get().strip() == "Local boundary":
            self.boundary_name_var.set("Two-point local curve")

        self.show_boundary_var.set(True)
        self.refresh_equation_label()
        self.refresh_graph(load_active_boundary=False)

    def _get_curve_control_points(self):
        p1_hr = _safe_float(self.point1_hr_var.get())
        p1_n = _safe_float(self.point1_n_var.get())
        p2_hr = _safe_float(self.point2_hr_var.get())
        p2_n = _safe_float(self.point2_n_var.get())

        points = []

        if p1_hr is not None and p1_n is not None and p1_hr > 0 and p1_n > 0:
            points.append((1, p1_hr, p1_n))

        if p2_hr is not None and p2_n is not None and p2_hr > 0 and p2_n > 0:
            points.append((2, p2_hr, p2_n))

        return points


    def _plot_curve_control_points(self):
        self.curve_point_artists = []

        if not self.edit_curve_points_var.get():
            return

        control_points = self._get_curve_control_points()

        for point_number, hr, n_value in control_points:
            artist = self.ax.scatter(
                [hr],
                [n_value],
                s=140,
                marker="D",
                edgecolors="black",
                linewidths=1.0,
                label=f"P{point_number}",
                zorder=10,
            )

            self.curve_point_artists.append((point_number, artist))

            self.ax.annotate(
                f"P{point_number}",
                (hr, n_value),
                textcoords="offset points",
                xytext=(8, 8),
                fontsize=9,
                fontweight="bold",
                zorder=11,
            )


    def _set_curve_point(self, point_number: int, hr: float, n_value: float):
        if hr <= 0 or n_value <= 0:
            return

        if point_number == 1:
            self.point1_hr_var.set(f"{hr:.6g}")
            self.point1_n_var.set(f"{n_value:.6g}")
        elif point_number == 2:
            self.point2_hr_var.set(f"{hr:.6g}")
            self.point2_n_var.set(f"{n_value:.6g}")


    def _get_nearest_curve_point_number(self, event, max_pixel_distance: float = 18.0):
        control_points = self._get_curve_control_points()

        if not control_points:
            return None

        nearest_point_number = None
        nearest_distance = None

        mouse_x = event.x
        mouse_y = event.y

        for point_number, point_hr, point_n in control_points:
            point_x, point_y = self.ax.transData.transform((point_hr, point_n))

            distance = ((mouse_x - point_x) ** 2 + (mouse_y - point_y) ** 2) ** 0.5

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_point_number = point_number

        if nearest_distance is None:
            return None

        if nearest_distance > max_pixel_distance:
            return None

        return nearest_point_number


    def _try_rebuild_curve_from_points(self):
        p1_hr = _safe_float(self.point1_hr_var.get())
        p1_n = _safe_float(self.point1_n_var.get())
        p2_hr = _safe_float(self.point2_hr_var.get())
        p2_n = _safe_float(self.point2_n_var.get())

        if (
            p1_hr is None or p1_n is None
            or p2_hr is None or p2_n is None
            or p1_hr <= 0 or p1_n <= 0
            or p2_hr <= 0 or p2_n <= 0
        ):
            return

        self.build_boundary_from_two_points()


    def on_graph_mouse_press(self, event):
        if not self.edit_curve_points_var.get():
            return

        if event.inaxes != self.ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        hr = float(event.xdata)
        n_value = float(event.ydata)

        if hr <= 0 or n_value <= 0:
            return

        p1_hr = _safe_float(self.point1_hr_var.get())
        p1_n = _safe_float(self.point1_n_var.get())
        p2_hr = _safe_float(self.point2_hr_var.get())
        p2_n = _safe_float(self.point2_n_var.get())

        if p1_hr is None or p1_n is None or p1_hr <= 0 or p1_n <= 0:
            self.dragged_curve_point = 1
            self._set_curve_point(1, hr, n_value)
            self.refresh_graph(load_active_boundary=False)
            return

        if p2_hr is None or p2_n is None or p2_hr <= 0 or p2_n <= 0:
            self.dragged_curve_point = 2
            self._set_curve_point(2, hr, n_value)
            self._try_rebuild_curve_from_points()
            return

        self.dragged_curve_point = self._get_nearest_curve_point_number(event)

        if self.dragged_curve_point is None:
            return



    def on_graph_mouse_move(self, event):
        if not self.edit_curve_points_var.get():
            return

        if self.dragged_curve_point is None:
            return

        if event.inaxes != self.ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        hr = float(event.xdata)
        n_value = float(event.ydata)

        if hr <= 0 or n_value <= 0:
            return

        self._set_curve_point(self.dragged_curve_point, hr, n_value)
        self._try_rebuild_curve_from_points()


    def on_graph_mouse_release(self, event):
        self.dragged_curve_point = None

    def clear_edit_points(self):
        self.point1_hr_var.set("")
        self.point1_n_var.set("")
        self.point2_hr_var.set("")
        self.point2_n_var.set("")

        self.dragged_curve_point = None

        if self.edit_curve_points_var.get():
            self.frozen_axis_limits = (
                self.ax.get_xlim(),
                self.ax.get_ylim(),
            )

        self.refresh_graph(load_active_boundary=False)


    def refresh_graph(self, load_active_boundary: bool = True):
        current_axis_limits = None

        if self.edit_curve_points_var.get() and self.frozen_axis_limits is not None:
            current_axis_limits = self.frozen_axis_limits

        self.refresh_filter_lists()

        if load_active_boundary:
            self.load_active_boundary_for_current_filters(show_message=False)

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

        self._plot_saved_inactive_curves(points)

        if self.show_boundary_var.get():
            self._plot_local_boundary(points)

        self._plot_curve_control_points()



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

        if current_axis_limits is not None:
            x_limits, y_limits = current_axis_limits
            self.ax.set_xlim(x_limits)
            self.ax.set_ylim(y_limits)

        self.summary_var.set(
            f"Shown points: {len(points)} / Filtered rows: {len(rows)} | "
            f"States: {', '.join(sorted(plotted_states)) if plotted_states else 'None'}"
        )

        self.canvas.draw()


    def load_active_boundary_for_current_filters(self, show_message: bool = False):
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
            self.show_boundary_var.set(False)
            return

        self._load_boundary_fields(boundary)
        self.show_boundary_var.set(True)
        self.saved_boundary_var.set(self._make_boundary_display_name(boundary))

        if show_message:
            messagebox.showinfo("Curve loaded", "Active curve was loaded for current filters.")

    def _plot_local_boundary(self, points: list[dict]):
        slope = _safe_float(self.boundary_slope_var.get())
        intercept = _safe_float(self.boundary_intercept_var.get())
        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if slope is None or intercept is None:
            return
        if mode == "power" and intercept <= 0:
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

        valid_mask = y_values > 0
        if not np.any(valid_mask):
            return

        label = self.boundary_name_var.get().strip() or "Local curve"
        self.ax.plot(
            x_values[valid_mask],
            y_values[valid_mask],
            linestyle="--",
            linewidth=2.0,
            color="black",
            label=f"{label}: {equation_label}",
        )

    def _plot_saved_inactive_curves(self, points: list[dict]):
        if not self.show_inactive_curves_var.get():
            return

        context = self._get_exact_curve_context()

        if context is None:
            return

        project, domain, surface = context

        saved_curves = list_boundaries_exact(
            project=project,
            domain=domain,
            surface=surface,
            boundary_type="Stable-Unstable",
            db_path=self.database_path,
            active_only=False,
        )

        x_min, x_max = self._get_boundary_x_range(points)

        if x_min <= 0 or x_max <= 0 or x_min >= x_max:
            return

        x_values = np.linspace(x_min, x_max, 300)

        for row in saved_curves:
            is_active = int(row.get("is_active", 0) or 0) == 1

            if is_active:
                continue

            slope = _safe_float(row.get("slope"))
            intercept = _safe_float(row.get("intercept"))
            mode = str(row.get("mode", "linear") or "linear").strip().lower()
            name = row.get("boundary_name", "") or "Inactive curve"

            if slope is None or intercept is None:
                continue

            if mode == "power":
                if intercept <= 0:
                    continue

                y_values = intercept * (x_values ** slope)
                equation_label = f"{name}: N = {intercept:g}×HR^{slope:g}"
            else:
                y_values = slope * x_values + intercept
                equation_label = f"{name}: N = {slope:g}×HR + {intercept:g}"

            valid_x = []
            valid_y = []

            for x, y in zip(x_values, y_values):
                if y > 0:
                    valid_x.append(x)
                    valid_y.append(y)

            if not valid_x:
                continue

            self.ax.plot(
                valid_x,
                valid_y,
                linestyle=":",
                linewidth=1.2,
                color="gray",
                alpha=0.7,
                label=equation_label,
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

            if hr is None or n is None or hr <= 0 or n <= 0:
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
        counts = {"Stable": 0, "Unstable": 0, "Caved": 0, "Unknown": 0}
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

    def _make_boundary_display_name(self, row: dict) -> str:
        active = "ACTIVE" if int(row.get("is_active", 0) or 0) == 1 else "inactive"
        boundary_type = row.get("boundary_type", "") or "Stable-Unstable"
        mode = row.get("mode", "") or "linear"
        name = row.get("boundary_name", "") or "Unnamed curve"
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

    def _load_boundary_fields(self, row: dict):
        self.boundary_name_var.set(row.get("boundary_name", "Local curve"))
        self.boundary_mode_var.set(str(row.get("mode", "linear") or "linear"))
        self.boundary_slope_var.set(str(row.get("slope", "1.0")))
        self.boundary_intercept_var.set(str(row.get("intercept", "0.0")))
        self.boundary_comment_var.set(row.get("comment", ""))
        self.refresh_equation_label()

    def save_current_boundary(self):
        context = self._get_exact_curve_context()
        if context is None:
            messagebox.showerror(
                "Save curve error",
                "Select exact Project, Domain and Surface before saving a local curve.",
            )
            return

        slope = _safe_float(self.boundary_slope_var.get())
        intercept = _safe_float(self.boundary_intercept_var.get())
        mode = self.boundary_mode_var.get().strip().lower() or "linear"

        if slope is None or intercept is None:
            messagebox.showerror(
                "Save curve error",
                "Curve slope and intercept must be valid numbers.",
            )
            return

        if mode == "power" and intercept <= 0:
            messagebox.showerror(
                "Save curve error",
                "For power curve, b/intercept is coefficient k and must be greater than zero.",
            )
            return

        boundary_name = self.boundary_name_var.get().strip()
        if not boundary_name:
            messagebox.showerror("Save curve error", "Curve name cannot be empty.")
            return

        project, domain, surface = context
        row = {
            "project": project,
            "domain": domain,
            "surface": surface,
            "boundary_name": boundary_name,
            "boundary_type": "Stable-Unstable",
            "mode": mode,
            "slope": slope,
            "intercept": intercept,
            "percentile": None,
            "margin": None,
            "is_standard": 0,
            "is_active": 1,
            "comment": self.boundary_comment_var.get().strip(),
        }

        boundary_id = upsert_boundary(row, self.database_path)
        set_active_boundary(boundary_id, self.database_path)
        self.refresh_saved_boundaries()

        saved_row = next(
            (boundary for boundary in self.saved_boundaries if int(boundary.get("id", -1)) == boundary_id),
            row,
        )
        self.saved_boundary_var.set(self._make_boundary_display_name(saved_row))
        self.show_boundary_var.set(True)
        self.refresh_graph(load_active_boundary=False)

        messagebox.showinfo(
            "Curve saved",
            f"Curve was saved to SQLite database:\n{self.database_path}",
        )

    def load_selected_boundary(self):
        row = self._get_selected_boundary_row()
        if row is None:
            messagebox.showinfo("No curve selected", "Select a saved curve first.")
            return

        project = row.get("project", "")
        domain = row.get("domain", "")
        surface = row.get("surface", "")

        self.project_filter_var.set(project if project else ALL_VALUE)
        self.domain_filter_var.set(domain if domain else ALL_VALUE)
        self.surface_filter_var.set(surface if surface else ALL_VALUE)

        self._load_boundary_fields(row)
        self.show_boundary_var.set(True)
        self.refresh_filter_lists()
        self.refresh_graph(load_active_boundary=False)

    def set_selected_boundary_active(self):
        row = self._get_selected_boundary_row()
        if row is None:
            messagebox.showinfo("No curve selected", "Select a saved curve first.")
            return

        boundary_id = row.get("id")
        if boundary_id is None:
            messagebox.showerror("Set active error", "Selected curve has no SQLite id.")
            return

        set_active_boundary(int(boundary_id), self.database_path)
        self.refresh_saved_boundaries()
        self.load_active_boundary_for_current_filters(show_message=False)
        self.refresh_graph(load_active_boundary=False)

        messagebox.showinfo(
            "Curve activated",
            "Selected curve is now active for this Project / Domain / Surface.",
        )

    def deactivate_selected_boundary(self):
        row = self._get_selected_boundary_row()
        if row is None:
            messagebox.showinfo("No curve selected", "Select a saved curve first.")
            return

        boundary_id = row.get("id")
        if boundary_id is None:
            messagebox.showerror("Deactivate error", "Selected curve has no SQLite id.")
            return

        deactivate_boundary(int(boundary_id), self.database_path)
        self.refresh_saved_boundaries()
        self.show_boundary_var.set(False)
        self.refresh_graph(load_active_boundary=False)

        messagebox.showinfo("Curve deactivated", "Selected curve was deactivated.")

    def delete_selected_boundary(self):
        row = self._get_selected_boundary_row()
        if row is None:
            messagebox.showinfo("No curve selected", "Select a saved curve first.")
            return

        boundary_id = row.get("id")
        if boundary_id is None:
            messagebox.showerror("Delete curve error", "Selected curve has no SQLite id.")
            return

        answer = messagebox.askyesno(
            "Delete curve",
            f"Delete saved curve?\n\n{self._make_boundary_display_name(row)}",
        )
        if not answer:
            return

        delete_boundary(int(boundary_id), self.database_path)
        self.refresh_saved_boundaries()
        self.show_boundary_var.set(False)
        self.refresh_graph(load_active_boundary=False)

        messagebox.showinfo("Curve deleted", "Saved curve was deleted from SQLite database.")

    def export_png(self):
        rows = self.get_filtered_rows()
        points = self._prepare_points(rows)

        if not points and not self.show_boundary_var.get():
            messagebox.showinfo("No graph", "There are no valid points to export.")
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
            messagebox.showinfo("Export complete", f"Graph was exported to:\n{output_path}")
        except Exception as error:
            messagebox.showerror("Export error", str(error))

    def on_edit_points_toggle(self):
        if self.edit_curve_points_var.get():
            self.frozen_axis_limits = (
                self.ax.get_xlim(),
                self.ax.get_ylim(),
            )
        else:
            self.frozen_axis_limits = None

        self.refresh_graph(load_active_boundary=False)
