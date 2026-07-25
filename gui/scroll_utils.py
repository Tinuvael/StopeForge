"""Small Tkinter helpers for canvas-based vertical mouse-wheel scrolling.

The helper binds wheel events only while the pointer is inside the supplied
scrollable area.  This avoids a permanent global ``bind_all`` that can steal
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
    follows the visible canvas width. Wheel events are bound to the containing
    window and handled only while the pointer is over the canvas or one of the
    inner frame's descendants. Windows/macOS ``<MouseWheel>`` and Linux
    ``<Button-4>/<Button-5>`` events are supported.

    Returns the canvas window item id for callers that need it.
    """

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    state: dict[str, dict[str, str]] = {"bindings": {}}
    toplevel = canvas.winfo_toplevel()

    def update_scrollregion(_event: tk.Event[Any] | None = None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))

    def update_inner_width(event: tk.Event[Any]) -> None:
        canvas.itemconfigure(window_id, width=event.width)

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
        target = canvas.winfo_containing(canvas.winfo_pointerx(), canvas.winfo_pointery())
        if target is not None and _widget_has_native_vertical_scroll(target):
            return None

        if target is None or not _is_canvas_content(target):
            return None

        units = scroll_units_from_event(event)
        if units:
            canvas.yview_scroll(units, "units")
            return "break"
        return None

    def _is_canvas_content(widget: tk.Widget) -> bool:
        current: tk.Widget | None = widget
        while current is not None:
            if current in (canvas, scrollable_frame):
                return True
            current = getattr(current, "master", None)
        return False

    def unbind_wheel(_event: tk.Event[Any] | None = None) -> None:
        bindings = state["bindings"]
        for sequence, func_id in list(bindings.items()):
            try:
                toplevel.unbind(sequence, func_id)
            except tk.TclError:
                pass
            bindings.pop(sequence, None)

    scrollable_frame.bind("<Configure>", update_scrollregion, add="+")
    canvas.bind("<Configure>", update_inner_width, add="+")
    bindings = state["bindings"]
    bindings["<MouseWheel>"] = toplevel.bind("<MouseWheel>", on_mousewheel, add="+")
    bindings["<Button-4>"] = toplevel.bind("<Button-4>", on_mousewheel, add="+")
    bindings["<Button-5>"] = toplevel.bind("<Button-5>", on_mousewheel, add="+")
    canvas.bind("<Destroy>", unbind_wheel, add="+")
    canvas.after_idle(update_scrollregion)

    return window_id
