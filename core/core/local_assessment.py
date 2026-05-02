from db.boundary_repository import find_active_boundary_exact
from db.connection import DEFAULT_PROJECT_DB_PATH
from core.models import SurfaceType, StabilityState


def calculate_surface_hydraulic_radius(surface_type: SurfaceType, stope) -> float:
    height = stope.stope_height_m
    width = stope.stope_width_m
    span = stope.stope_span_m

    if surface_type == SurfaceType.CROWN:
        a = width
        b = span
    elif surface_type in (SurfaceType.HANGING_WALL, SurfaceType.FOOTWALL):
        a = height
        b = span
    elif surface_type == SurfaceType.END_WALL:
        a = height
        b = width
    else:
        raise ValueError(f"Unknown surface type: {surface_type}")

    if a <= 0 or b <= 0:
        raise ValueError("Surface dimensions must be greater than zero.")

    return (a * b) / (2 * (a + b))


def assess_against_linear_boundary(
    stability_number_n: float,
    hydraulic_radius: float,
    boundary: dict,
) -> tuple[StabilityState, float]:
    slope = float(boundary["slope"])
    intercept = float(boundary["intercept"])

    boundary_n = slope * hydraulic_radius + intercept

    if boundary_n <= 0:
        return StabilityState.UNKNOWN, boundary_n

    if stability_number_n >= boundary_n:
        return StabilityState.STABLE, boundary_n

    return StabilityState.UNSTABLE, boundary_n


def assess_surface_local(
    project: str,
    domain: str,
    surface: str,
    stability_number_n: float,
    hydraulic_radius: float,
    db_path=DEFAULT_PROJECT_DB_PATH,
) -> tuple[StabilityState, str, float | None]:
    boundary = find_active_boundary_exact(
    project=project,
    domain=domain,
    surface=surface,
    boundary_type="Stable-Unstable",
    db_path=db_path,
)


    if boundary is None:
        return StabilityState.UNKNOWN, "Not found", None

    local_state, boundary_n = assess_against_linear_boundary(
        stability_number_n=stability_number_n,
        hydraulic_radius=hydraulic_radius,
        boundary=boundary,
    )

    boundary_name = boundary.get("boundary_name", "Local boundary")

    return local_state, boundary_name, boundary_n
