from pathlib import Path

from core.models import StabilityState
from db.connection import DEFAULT_PROJECT_DB_PATH
from db.boundary_repository import find_active_boundary_exact


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


def _get_boundary_float(boundary: dict, keys: list[str]) -> float | None:
    for key in keys:
        if key in boundary:
            value = _safe_float(boundary.get(key))

            if value is not None:
                return value

    return None


def calculate_boundary_n(
    first,
    second=None,
    third=None,
    mode: str = "linear",
) -> float | None:
    """
    Calculate boundary N.

    Supported call styles:

    Current test/UI style:
        calculate_boundary_n(hydraulic_radius, boundary_dict)

    Alternative internal style:
        calculate_boundary_n(boundary_dict, hydraulic_radius)

    Old numeric style:
        calculate_boundary_n(slope, intercept, hydraulic_radius)
        calculate_boundary_n(slope, intercept, hydraulic_radius, mode="power")
    """

    # Style 1:
    # calculate_boundary_n(hr, boundary_dict)
    if isinstance(second, dict):
        hr = _safe_float(first)
        boundary = second

        slope = _safe_float(boundary.get("slope"))
        intercept = _safe_float(boundary.get("intercept"))
        curve_mode = str(boundary.get("mode", "linear") or "linear").strip().lower()

    # Style 2:
    # calculate_boundary_n(boundary_dict, hr)
    elif isinstance(first, dict):
        boundary = first
        hr = _safe_float(second)

        slope = _safe_float(boundary.get("slope"))
        intercept = _safe_float(boundary.get("intercept"))
        curve_mode = str(boundary.get("mode", "linear") or "linear").strip().lower()

    # Style 3:
    # calculate_boundary_n(slope, intercept, hr)
    else:
        slope = _safe_float(first)
        intercept = _safe_float(second)
        hr = _safe_float(third)
        curve_mode = str(mode or "linear").strip().lower()

    if slope is None or intercept is None or hr is None:
        return None

    if hr <= 0:
        return None

    if curve_mode == "power":
        # N = k * HR^a
        # slope = a
        # intercept = k
        if intercept <= 0:
            raise ValueError("Power curve coefficient k must be greater than zero.")

        boundary_n = intercept * (hr ** slope)

    else:
        # N = a * HR + b
        boundary_n = slope * hr + intercept

    if boundary_n <= 0:
        return None

    return float(boundary_n)






def _get_first_valid_float(obj, field_names: list[str]) -> float | None:
    for field_name in field_names:
        value = getattr(obj, field_name, None)
        parsed = _safe_float(value)

        if parsed is not None:
            return parsed

    return None


def calculate_surface_hydraulic_radius(surface_type, stope) -> float:
    """
    Calculate hydraulic radius for stope surface.

    HR = Area / Perimeter

    Crown / Back:
        width x span

    Hanging wall / Footwall:
        height x span

    End wall:
        height x width
    """

    surface_name = getattr(surface_type, "value", str(surface_type))

    height = _get_first_valid_float(
        stope,
        [
            "stope_height_m",
            "height_m",
            "height",
        ],
    )

    width = _get_first_valid_float(
        stope,
        [
            "stope_width_m",
            "width_m",
            "ore_thickness_m",
            "width",
        ],
    )

    span = _get_first_valid_float(
        stope,
        [
            "stope_span_m",
            "span_m",
            "strike_length_m",
            "span",
        ],
    )

    if height is None or width is None or span is None:
        raise ValueError("Stope height, width and span must be valid numbers.")

    if height <= 0 or width <= 0 or span <= 0:
        raise ValueError("Stope height, width and span must be greater than zero.")

    if surface_name in ("Crown", "Back", "Crown / Back"):
        a = width
        b = span
    elif surface_name in ("Hanging wall", "Footwall"):
        a = height
        b = span
    elif surface_name == "End wall":
        a = height
        b = width
    else:
        a = height
        b = span

    area = a * b
    perimeter = 2.0 * (a + b)

    return area / perimeter




def assess_surface_local(
    project: str,
    domain: str,
    surface: str,
    stability_number_n: float,
    hydraulic_radius: float,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> tuple[StabilityState, str | None, float | None]:
    """
    Assess surface using active local curves.

    Priority:
    1. Stable-Unstable boundary
    2. Unstable-Caved boundary

    Returned tuple:
    - local stability state
    - boundary name used for the final decision
    - boundary N used for the final decision
    """
    actual_n = _safe_float(stability_number_n)
    actual_hr = _safe_float(hydraulic_radius)

    if actual_n is None or actual_hr is None:
        return StabilityState.UNKNOWN, None, None

    stable_unstable_boundary = find_active_boundary_exact(
        project=project,
        domain=domain,
        surface=surface,
        boundary_type="Stable-Unstable",
        db_path=db_path,
    )

    unstable_caved_boundary = find_active_boundary_exact(
        project=project,
        domain=domain,
        surface=surface,
        boundary_type="Unstable-Caved",
        db_path=db_path,
    )

    stable_unstable_n = calculate_boundary_n(
        stable_unstable_boundary,
        actual_hr,
    )

    unstable_caved_n = calculate_boundary_n(
        unstable_caved_boundary,
        actual_hr,
    )

    # Both boundaries exist.
    if stable_unstable_n is not None and unstable_caved_n is not None:
        if actual_n >= stable_unstable_n:
            return (
                StabilityState.STABLE,
                stable_unstable_boundary.get("boundary_name"),
                stable_unstable_n,
            )

        if actual_n < unstable_caved_n:
            return (
                StabilityState.CAVED,
                unstable_caved_boundary.get("boundary_name"),
                unstable_caved_n,
            )

        return (
            StabilityState.UNSTABLE,
            stable_unstable_boundary.get("boundary_name"),
            stable_unstable_n,
        )

    # Only Stable-Unstable boundary exists.
    if stable_unstable_n is not None:
        if actual_n >= stable_unstable_n:
            return (
                StabilityState.STABLE,
                stable_unstable_boundary.get("boundary_name"),
                stable_unstable_n,
            )

        return (
            StabilityState.UNSTABLE,
            stable_unstable_boundary.get("boundary_name"),
            stable_unstable_n,
        )

    # Only Unstable-Caved boundary exists.
    if unstable_caved_n is not None:
        if actual_n < unstable_caved_n:
            return (
                StabilityState.CAVED,
                unstable_caved_boundary.get("boundary_name"),
                unstable_caved_n,
            )

        return (
            StabilityState.UNSTABLE,
            unstable_caved_boundary.get("boundary_name"),
            unstable_caved_n,
        )

    return StabilityState.UNKNOWN, "Not found", None
