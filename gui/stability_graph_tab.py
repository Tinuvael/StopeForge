import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


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

        self.project_filter_var = tk.StringVar(value=ALL_VALUE)
        self.domain_filter_var = tk.StringVar(value=ALL_VALUE)
        self.surface_filter_var = tk.StringVar(value=ALL_VALUE)
        self.observed_filter_var = tk.StringVar(value=ALL_VALUE)

        self.log_x_var = tk.BooleanVar(value=True)
        self.log_y_var = tk.BooleanVar(value=True)
        self.show_labels_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_title_bar(container)
        self._build_filters(container)
        self._build_graph(container)
        self.refresh_filters()
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
            command=self.refresh_filters,
        ).grid(row=1, column=8, padx=6, pady=6)

        for combo in (
            self.project_filter_combo,
            self.domain_filter_combo,
            self.surface_filter_combo,
            self.observed_filter_combo,
        ):
            combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_graph())

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

    def _get_all_rows(self) -> list[dict]:
        if self.get_case_rows_callback is None:
            return []

        return self.get_case_rows_callback()

    def refresh_filters(self):
        rows = self._get_all_rows()

        projects = sorted({row.get("project", "") for row in rows if row.get("project", "")})
        domains = sorted({row.get("domain", "") for row in rows if row.get("domain", "")})
        surfaces = sorted({row.get("surface", "") for row in rows if row.get("surface", "")})
        observed_states = sorted(
            {row.get("observed_state", "Unknown") for row in rows if row.get("observed_state", "Unknown")}
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

    def refresh_graph(self):
        self.refresh_filters()

        rows = self.get_filtered_rows()
        points = self._prepare_points(rows)

        self.ax.clear()

        self.ax.set_title("Mathews–Potvin Stability Graph")
        self.ax.set_xlabel("Hydraulic Radius / Shape Factor HR, m")
        self.ax.set_ylabel("Mathews Stability Number N")

        self.ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)

        if self.log_x_var.get():
            self.ax.set_xscale("log")

        if self.log_y_var.get():
            self.ax.set_yscale("log")

        if not points:
            self.ax.text(
                0.5,
                0.5,
                "No valid case history points to plot.\nAdd cases or check filters.",
                transform=self.ax.transAxes,
                ha="center",
                va="center",
                fontsize=11,
            )
            self.summary_var.set(f"Shown points: 0 / Filtered rows: {len(rows)}")
            self.canvas.draw()
            return

        plotted_states = set()

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

        self.ax.legend(loc="best")
        self.figure.tight_layout()

        self.summary_var.set(
            f"Shown points: {len(points)} / Filtered rows: {len(rows)} | "
            f"States: {', '.join(sorted(plotted_states)) if plotted_states else 'None'}"
        )

        self.canvas.draw()

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

    def export_png(self):
        rows = self.get_filtered_rows()
        points = self._prepare_points(rows)

        if not points:
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
