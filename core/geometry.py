from core.models import SurfaceType


def calculate_area(height_m: float, length_m: float) -> float:
    if height_m <= 0 or length_m <= 0:
        raise ValueError("Surface dimensions must be greater than zero.")

    return height_m * length_m


def calculate_perimeter(height_m: float, length_m: float) -> float:
    if height_m <= 0 or length_m <= 0:
        raise ValueError("Surface dimensions must be greater than zero.")

    return 2 * (height_m + length_m)


def calculate_hydraulic_radius(height_m: float, length_m: float) -> float:
    area = calculate_area(height_m, length_m)
    perimeter = calculate_perimeter(height_m, length_m)

    return area / perimeter


def calculate_surface_hydraulic_radius(
    surface_type: SurfaceType,
    stope_height_m: float,
    stope_width_m: float,
    stope_span_m: float,
) -> float:
    """
    Calculate actual hydraulic radius for each stope surface.

    Crown:
        area = span * width

    Hanging wall / Footwall:
        area = height * span

    End wall:
        area = height * width
    """
    if surface_type == SurfaceType.CROWN:
        return calculate_hydraulic_radius(stope_width_m, stope_span_m)

    if surface_type in (SurfaceType.HANGING_WALL, SurfaceType.FOOTWALL):
        return calculate_hydraulic_radius(stope_height_m, stope_span_m)

    if surface_type == SurfaceType.END_WALL:
        return calculate_hydraulic_radius(stope_height_m, stope_width_m)

    raise ValueError(f"Unknown surface type: {surface_type}")
