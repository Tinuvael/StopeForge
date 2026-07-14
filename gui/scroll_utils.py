"""Small Tkinter helpers for canvas-based vertical mouse-wheel scrolling.

The helper binds wheel events to a private bindtag that is added only to the
canvas and its form children. This avoids a global ``bind_all`` that can steal
mouse-wheel events from other windows or from Matplotlib widgets.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


_NATIVE_SCROLL_CLASSES = {
    "Text",
    "Listbox",
    "Treeview",
}


def _widget_has_native_vertical_scroll(widget: tk.Widget) -> bool:
    """Return True for widgets that should keep their own wheel handling."""
    widget_class = widget.winfo_class()

    if widget_class in _NATIVE_SCROLL_CLASSES:
        return True

    # ttk Combobox popdowns and Spinbox-like controls can have their own wheel
    # behavior depending on platform/theme.  Entries and Comboboxes in normal
    # forms do not need vertical scrolling, so they are intentionally allowed to
    # bubble to the parent canvas.
    return False


def _event_inside_widget(event: tk.Event[Any], widget: tk.Widget) -> bool:
    """Check whether the pointer coordinates from a wheel event are inside widget."""
    try:
        x = widget.winfo_pointerx()
        y = widget.winfo_pointery()
        root_x = widget.winfo_rootx()
        root_y = widget.winfo_rooty()
        return root_x <= x < root_x + widget.winfo_width() and root_y <= y < root_y + widget.winfo_height()
    except tk.TclError:
        return False


def enable_mousewheel_scrolling(canvas: tk.Canvas, scrollable_frame: ttk.Frame | tk.Frame) -> int:
    """Enable safe mouse-wheel scrolling for a canvas/inner-frame pair.

    The canvas scrollregion follows the inner frame, and the inner frame width
    follows the visible canvas width. Windows/macOS ``<MouseWheel>`` and Linux
    ``<Button-4>/<Button-5>`` events are supported.

    Returns the canvas window item id for callers that need it.
    """

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    wheel_tag = f"{canvas.winfo_id()}MouseWheelScroll"
    state = {"active": False}

    def canvas_height() -> int:
        return max(canvas.winfo_height(), 1)

    def content_height() -> int:
        return max(scrollable_frame.winfo_reqheight(), scrollable_frame.winfo_height(), 1)

    def clamp_yview() -> None:
        """Keep the visible area inside content after window resize."""
        height = content_height()
        visible_height = canvas_height()

        if height <= visible_height:
            canvas.yview_moveto(0)
            return

        first, last = canvas.yview()
        if last > 1.0:
            canvas.yview_moveto(max(0.0, 1.0 - visible_height / height))
        elif first < 0.0:
            canvas.yview_moveto(0)

    def update_scrollregion(_event: tk.Event[Any] | None = None) -> None:
        width = max(canvas.winfo_width(), scrollable_frame.winfo_reqwidth(), 1)
        height = max(content_height(), canvas_height())
        canvas.configure(scrollregion=(0, 0, width, height))
        canvas.after_idle(clamp_yview)

    def update_inner_width(event: tk.Event[Any]) -> None:
        canvas.itemconfigure(window_id, width=event.width)
        update_scrollregion()

    def scroll_units_from_event(event: tk.Event[Any]) -> int:
        if getattr(event, "num", None) == 4:
            return -1
        if getattr(event, "num", None) == 5:
            return 1

        delta = getattr(event, "delta", 0)
        if delta == 0:
            return 0

        # Windows normally sends +/-120. Some touchpads send smaller deltas, so
        # keep at least one unit when a non-zero wheel event arrives.
        units = int(-delta / 120)
        if units == 0:
            units = -1 if delta > 0 else 1
        return units

    def on_mousewheel(event: tk.Event[Any]) -> str | None:
        if not state["active"]:
            return None

        target = canvas.winfo_containing(canvas.winfo_pointerx(), canvas.winfo_pointery())
        if target is not None and _widget_has_native_vertical_scroll(target):
            return None

        if not _event_inside_widget(event, canvas):
            return None

        if content_height() <= canvas_height():
            canvas.yview_moveto(0)
            return "break"

        units = scroll_units_from_event(event)
        if units:
            canvas.yview_scroll(units, "units")
            canvas.after_idle(clamp_yview)
            return "break"
        return None

    def activate_wheel(_event: tk.Event[Any] | None = None) -> None:
        state["active"] = True

    def deactivate_wheel(event: tk.Event[Any] | None = None) -> None:
        if event is not None and _event_inside_widget(event, canvas):
            return
        state["active"] = False

    def add_wheel_tag(widget: tk.Widget) -> None:
        if _widget_has_native_vertical_scroll(widget):
            return

        bindtags = widget.bindtags()
        if wheel_tag not in bindtags:
            widget.bindtags((wheel_tag, *bindtags))

    def tag_descendants(widget: tk.Widget) -> None:
        add_wheel_tag(widget)

        for child in widget.winfo_children():
            tag_descendants(child)

    def refresh_bindtags(_event: tk.Event[Any] | None = None) -> None:
        tag_descendants(canvas)
        tag_descendants(scrollable_frame)

    canvas.bind_class(wheel_tag, "<Enter>", activate_wheel, add="+")
    canvas.bind_class(wheel_tag, "<Leave>", deactivate_wheel, add="+")
    canvas.bind_class(wheel_tag, "<MouseWheel>", on_mousewheel, add="+")
    canvas.bind_class(wheel_tag, "<Button-4>", on_mousewheel, add="+")
    canvas.bind_class(wheel_tag, "<Button-5>", on_mousewheel, add="+")

    scrollable_frame.bind("<Configure>", update_scrollregion, add="+")
    scrollable_frame.bind("<Map>", refresh_bindtags, add="+")
    canvas.bind("<Configure>", update_inner_width, add="+")
    canvas.bind("<Leave>", deactivate_wheel, add="+")

    canvas.after_idle(refresh_bindtags)
    canvas.after_idle(update_scrollregion)

    return window_id
