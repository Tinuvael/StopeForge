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
    follows the visible canvas width. Wheel events are bound with ``bind_all``
    only while the pointer is over the scrollable area, then unbound on leave.
    Windows/macOS ``<MouseWheel>`` and Linux ``<Button-4>/<Button-5>`` events are
    supported.

    Returns the canvas window item id for callers that need it.
    """

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    state: dict[str, bool | dict[str, str]] = {"active": False, "bindings": {}}

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

        if not _event_inside_widget(event, canvas):
            return None

        units = scroll_units_from_event(event)
        if units:
            canvas.yview_scroll(units, "units")
            return "break"
        return None

    def bind_wheel(_event: tk.Event[Any] | None = None) -> None:
        if state["active"]:
            return
        state["active"] = True
        bindings = state["bindings"]
        assert isinstance(bindings, dict)
        bindings["<MouseWheel>"] = canvas.bind_all("<MouseWheel>", on_mousewheel, add="+")
        bindings["<Button-4>"] = canvas.bind_all("<Button-4>", on_mousewheel, add="+")
        bindings["<Button-5>"] = canvas.bind_all("<Button-5>", on_mousewheel, add="+")

    def unbind_wheel(event: tk.Event[Any] | None = None) -> None:
        if not state["active"]:
            return
        if event is not None and _event_inside_widget(event, canvas):
            return
        state["active"] = False
        bindings = state["bindings"]
        assert isinstance(bindings, dict)
        for sequence, func_id in list(bindings.items()):
            try:
                canvas._unbind(("bind", "all"), sequence, func_id)
            except tk.TclError:
                pass
            bindings.pop(sequence, None)

    scrollable_frame.bind("<Configure>", update_scrollregion, add="+")
    canvas.bind("<Configure>", update_inner_width, add="+")
    canvas.bind("<Enter>", bind_wheel, add="+")
    scrollable_frame.bind("<Enter>", bind_wheel, add="+")
    canvas.bind("<Leave>", unbind_wheel, add="+")

    canvas.bind("<Destroy>", unbind_wheel, add="+")
    canvas.after_idle(update_scrollregion)

    return window_id
