import math
import tkinter as tk
from tkinter import ttk

from core.models import SurfaceType


STATUS_COLORS = {
    "stable": "#188038",
    "unstable": "#f9ab00",
    "caved": "#d93025",
}
UNKNOWN_COLOR = "#9aa0a6"


class StopeSectionSketch(ttk.Frame):
    """Canvas sketch for a schematic stope section in the calculation tab."""

    def __init__(self, parent):
        super().__init__(parent)
        self._result = None
        self.canvas = tk.Canvas(self, height=260, bg="white", highlightthickness=1, highlightbackground="#d0d0d0")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._redraw)
        self.draw_placeholder("Run a calculation to show the stope section sketch.")

    def draw_result(self, result):
        self._result = result
        self._redraw()

    def draw_placeholder(self, message="Cannot draw sketch: check stope geometry inputs."):
        self._result = None
        self.canvas.delete("all")
        self._draw_centered_message(message)

    def _redraw(self, _event=None):
        self.canvas.delete("all")

        if self._result is None:
            self._draw_centered_message("Run a calculation to show the stope section sketch.")
            return

        try:
            self._draw_sketch(self._result)
        except (TypeError, ValueError, OverflowError):
            self.canvas.delete("all")
            self._draw_centered_message("Cannot draw sketch: check stope geometry inputs.")

    def _draw_centered_message(self, message):
        width = max(self.canvas.winfo_width(), 320)
        height = max(self.canvas.winfo_height(), 220)
        self.canvas.create_text(
            width / 2,
            height / 2,
            text=message,
            fill="#555555",
            width=width - 40,
            font=("Segoe UI", 9, "italic"),
            justify="center",
        )
        self._draw_design_note(width, height)

    def _draw_sketch(self, result):
        stope = result.stope
        height_m = self._valid_positive(stope.stope_height_m)
        width_m = self._valid_positive(stope.stope_width_m)
        dip_deg = self._valid_dip(stope.average_dip_deg)
        status_colors = self._surface_status_colors(result)

        canvas_width = max(self.canvas.winfo_width(), 360)
        canvas_height = max(self.canvas.winfo_height(), 260)
        drawing_width = max(canvas_width - 150, 170)
        drawing_height = max(canvas_height - 85, 120)

        display_ratio, normalized = self._display_ratio(height_m / width_m)
        section_h = min(drawing_height, 190)
        section_w = section_h / display_ratio

        if section_w > drawing_width:
            section_w = drawing_width
            section_h = section_w * display_ratio

        section_w = max(45, section_w)
        section_h = max(70, section_h)

        # Shift the lower contact points to suggest dip without allowing extreme skew.
        dip_rad = math.radians(max(1.0, min(89.0, dip_deg)))
        skew = section_h / math.tan(dip_rad)
        max_skew = min(70, drawing_width * 0.28)
        skew = max(-max_skew, min(max_skew, skew))

        min_x = 25
        x0 = min_x + max(0, -skew)
        y0 = 34

        p_top_fw = (x0, y0)
        p_top_hw = (x0 + section_w, y0)
        p_bottom_hw = (x0 + section_w + skew, y0 + section_h)
        p_bottom_fw = (x0 + skew, y0 + section_h)

        self.canvas.create_polygon(
            *p_top_fw,
            *p_top_hw,
            *p_bottom_hw,
            *p_bottom_fw,
            fill="#eef3f8",
            outline="#5f6368",
            width=1,
        )

        self._draw_surface_line(p_top_hw, p_bottom_hw, status_colors[SurfaceType.HANGING_WALL], "HW", 14, 0)
        self._draw_surface_line(p_top_fw, p_bottom_fw, status_colors[SurfaceType.FOOTWALL], "FW", -16, 0)
        self._draw_surface_line(p_top_fw, p_top_hw, status_colors[SurfaceType.CROWN], "Crown", 0, -14)
        self.canvas.create_line(*p_bottom_fw, *p_bottom_hw, fill="#5f6368", width=2)

        text_x = 18
        text_y = y0 + section_h + 20
        self.canvas.create_text(
            text_x,
            text_y,
            text=f"Height {height_m:g} m  |  Width {width_m:g} m  |  Dip {dip_deg:g}°",
            anchor="w",
            fill="#3c4043",
            font=("Segoe UI", 8),
        )

        if normalized:
            self.canvas.create_text(
                text_x,
                text_y + 17,
                text="Extreme geometry ratio: sketch is displayed schematically.",
                anchor="w",
                fill="#8a5a00",
                font=("Segoe UI", 8, "italic"),
            )

        self._draw_end_wall_key(canvas_width, y0, status_colors[SurfaceType.END_WALL])
        self._draw_design_note(canvas_width, canvas_height)

    def _draw_surface_line(self, start, end, color, label, label_dx, label_dy):
        self.canvas.create_line(*start, *end, fill=color, width=5, capstyle=tk.ROUND)
        mid_x = (start[0] + end[0]) / 2 + label_dx
        mid_y = (start[1] + end[1]) / 2 + label_dy
        self.canvas.create_text(mid_x, mid_y, text=label, fill="#202124", font=("Segoe UI", 8, "bold"))

    def _draw_end_wall_key(self, canvas_width, y0, color):
        x = max(canvas_width - 118, 230)
        y = y0 + 12
        self.canvas.create_rectangle(x, y, x + 28, y + 28, fill=color, outline="#5f6368")
        self.canvas.create_text(x + 38, y + 14, text="End wall", anchor="w", fill="#202124", font=("Segoe UI", 8, "bold"))

    def _draw_design_note(self, canvas_width, canvas_height):
        self.canvas.create_text(
            12,
            canvas_height - 14,
            text="Schematic view only, not a design drawing.",
            anchor="w",
            fill="#5f6368",
            font=("Segoe UI", 8, "italic"),
        )

    @staticmethod
    def _surface_status_colors(result):
        colors = {surface_type: UNKNOWN_COLOR for surface_type in SurfaceType}

        for surface in getattr(result, "surfaces", []):
            state = getattr(getattr(surface, "stability_state", None), "value", None)
            colors[surface.surface_type] = status_to_color(state)

        return colors

    @staticmethod
    def _valid_positive(value):
        value = float(value)
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Geometry dimensions must be positive.")
        return value

    @staticmethod
    def _valid_dip(value):
        value = float(value)
        if not math.isfinite(value) or not 0 <= value <= 90:
            raise ValueError("Dip must be between 0 and 90 degrees.")
        return value

    @staticmethod
    def _display_ratio(real_ratio):
        min_ratio = 0.55
        max_ratio = 3.25
        display_ratio = max(min_ratio, min(max_ratio, real_ratio))
        return display_ratio, not math.isclose(display_ratio, real_ratio)


def status_to_color(status_text):
    status_key = str(status_text or "").strip().lower()
    return STATUS_COLORS.get(status_key, UNKNOWN_COLOR)
