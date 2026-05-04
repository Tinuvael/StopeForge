import math

from core.local_assessment import (
    calculate_surface_hydraulic_radius,
    assess_surface_local,
)


from core.mathews_factors import (
    calculate_joint_orientation_factor_b,
    calculate_stress_factor_a,
    calculate_surface_orientation_factor_c,
)
from core.models import (
    JointSet,
    StopeInput,
    SurfaceInput,
    SurfaceResult,
    StopeResult,
    StabilityState,
    SurfaceType,
)

from db.connection import DEFAULT_PROJECT_DB_PATH

def calculate_stability_number(
    q_prime: float,
    stress_factor_a: float,
    joint_factor_b: float,
    surface_factor_c: float,
) -> float:
    if q_prime <= 0:
        raise ValueError("Q' must be greater than zero.")
    if stress_factor_a <= 0:
        raise ValueError("A must be greater than zero.")
    if joint_factor_b <= 0:
        raise ValueError("B must be greater than zero.")
    if surface_factor_c <= 0:
        raise ValueError("C must be greater than zero.")

    return q_prime * stress_factor_a * joint_factor_b * surface_factor_c


def calculate_stable_hr_limit(stability_number_n: float) -> float:
    n = stability_number_n

    if n < 0.5:
        return 1.125 + 1.75 * n
    if n < 1:
        return 1.5 + n
    if n < 1.7:
        return 1.79 + 0.71 * n
    if n < 4:
        return 2.26 + 0.43 * n
    if n < 7:
        return 2.67 + 0.33 * n
    if n < 12:
        return 3.6 + 0.2 * n
    if n < 18:
        return 4.0 + 0.17 * n
    if n < 25:
        return 4.43 + 0.14 * n
    if n < 31:
        return 3.83 + 0.16 * n
    if n < 40:
        return 5.56 + 0.11 * n
    if n < 70:
        return 7.33 + 0.067 * n
    if n < 87:
        return 7.88 + 0.059 * n
    if n < 112:
        return 9.52 + 0.04 * n
    if n < 140:
        return 10.0 + 0.036 * n
    if n < 200:
        return 10.33 + 0.033 * n
    if n < 280:
        return 12.0 + 0.025 * n

    return 11.0 + 0.029 * n


def calculate_caving_hr_limit(stability_number_n: float) -> float:
    n = stability_number_n

    if n < 0.5:
        return 2.875 + 2.25 * n
    if n < 1:
        return 3.5 + n
    if n < 1.7:
        return 3.79 + 0.71 * n
    if n < 4:
        return 4.11 + 0.52 * n
    if n < 7:
        return 4.73 + 0.36 * n
    if n < 12:
        return 5.48 + 0.26 * n
    if n < 18:
        return 6.2 + 0.2 * n
    if n < 25:
        return 6.71 + 0.17 * n
    if n < 31:
        return 6.8 + 0.17 * n
    if n < 40:
        return 8.56 + 0.11 * n
    if n < 55:
        return 9 + 0.1 * n
    if n < 70:
        return 10.83 + 0.067 * n
    if n < 87:
        return 10.15 + 0.076 * n
    if n < 112:
        return 12.624 + 0.048 * n
    if n < 170:
        return 14 + 0.036 * n
    if n < 200:
        return 14.25 + 0.035 * n
    if n < 240:
        return 15 + 0.03125 * n
    if n < 280:
        return 13.5 + 0.0375 * n

    return 16 + 0.0286 * n


def _safe_sin_deg(angle_deg: float) -> float:
    value = math.sin(math.radians(angle_deg))
    if abs(value) < 1e-9:
        raise ValueError("Sin(angle) is too close to zero. Check surface angle.")
    return value


def _safe_cos_deg(angle_deg: float) -> float:
    value = math.cos(math.radians(angle_deg))
    if abs(value) < 1e-9:
        raise ValueError("Cos(angle) is too close to zero. Check crown angle.")
    return value


def calculate_stable_strike_length(
    surface_type: SurfaceType,
    surface_angle_deg: float,
    crown_angle_deg: float,
    stope_height_m: float,
    stope_width_m: float,
    equivalent_span_m: float,
) -> float:
    """
    Logic copied from the old FjordUG prototype.

    For walls:
        adjusted = height / sin(surface_angle)

    For crown and end wall:
        adjusted = span / cos(crown_angle)

    Here stope_width_m is used as the cross-section span from the old prototype.
    """
    if surface_type in (SurfaceType.HANGING_WALL, SurfaceType.FOOTWALL):
        adjusted = stope_height_m / _safe_sin_deg(surface_angle_deg)
    else:
        adjusted = stope_width_m / _safe_cos_deg(crown_angle_deg)

    if adjusted <= equivalent_span_m:
        return float("inf")

    return adjusted * equivalent_span_m / (adjusted - equivalent_span_m)


def classify_by_length(
    rating_length_m: float,
    stable_length_m: float,
    cave_length_m: float,
) -> StabilityState:
    if rating_length_m >= cave_length_m:
        return StabilityState.CAVED

    if stable_length_m < rating_length_m < cave_length_m:
        return StabilityState.UNSTABLE

    return StabilityState.STABLE


def get_worst_state(states: list[StabilityState]) -> StabilityState:
    priority = {
        StabilityState.UNKNOWN: 0,
        StabilityState.STABLE: 1,
        StabilityState.UNSTABLE: 2,
        StabilityState.CAVED: 3,
    }

    return max(states, key=lambda state: priority[state])


def calculate_stope_result(
    stope: StopeInput,
    surfaces: list[SurfaceInput],
    joint_sets: list[JointSet],
    calculation_mode: str = "Standard",
    db_path=DEFAULT_PROJECT_DB_PATH,
) -> StopeResult:

    auto_stress_factor_a = calculate_stress_factor_a(
    depth_m=stope.depth_m,
    unit_weight_t_m3=stope.unit_weight_t_m3,
    ucs_mpa=stope.ucs_mpa,
    )


    surface_by_type = {surface.surface_type: surface for surface in surfaces}

    required_surfaces = [
        SurfaceType.CROWN,
        SurfaceType.HANGING_WALL,
        SurfaceType.FOOTWALL,
        SurfaceType.END_WALL,
    ]

    for surface_type in required_surfaces:
        if surface_type not in surface_by_type:
            raise ValueError(f"Missing surface: {surface_type.value}")

    crown_angle = surface_by_type[SurfaceType.CROWN].dip_deg
    hanging_wall_angle = surface_by_type[SurfaceType.HANGING_WALL].dip_deg
    end_wall_angle = surface_by_type[SurfaceType.END_WALL].dip_deg

    endwall_dip_direction = (stope.hanging_wall_dip_direction_deg - 90) % 360

    surface_dip_directions = {
        SurfaceType.CROWN: stope.hanging_wall_dip_direction_deg,
        SurfaceType.HANGING_WALL: stope.hanging_wall_dip_direction_deg,
        SurfaceType.FOOTWALL: stope.hanging_wall_dip_direction_deg,
        SurfaceType.END_WALL: endwall_dip_direction,
    }

    surface_results: list[SurfaceResult] = []

    for surface in surfaces:
        surface_dip_direction = surface_dip_directions[surface.surface_type]

        stress_factor_a = (
                surface.stress_factor_a
                if surface.stress_factor_a is not None
                else auto_stress_factor_a
        )

        if stress_factor_a <= 0:
            raise ValueError(f"{surface.surface_type.value}: A must be greater than zero.")


        joint_factor_b = calculate_joint_orientation_factor_b(
            surface_dip_deg=surface.dip_deg,
            surface_dip_direction_deg=surface_dip_direction,
            joint_sets=joint_sets,
        )

        surface_factor_c = calculate_surface_orientation_factor_c(surface.dip_deg)

        stability_number_n = calculate_stability_number(
            q_prime=surface.q_prime,
            stress_factor_a=stress_factor_a,
            joint_factor_b=joint_factor_b,
            surface_factor_c=surface_factor_c,
        )

        hr_stable = calculate_stable_hr_limit(stability_number_n)
        hr_caving = calculate_caving_hr_limit(stability_number_n)

        equivalent_stable_span = hr_stable * 2
        equivalent_caving_span = hr_caving * 2

        stable_strike_length = calculate_stable_strike_length(
            surface_type=surface.surface_type,
            surface_angle_deg=surface.dip_deg,
            crown_angle_deg=crown_angle,
            stope_height_m=stope.stope_height_m,
            stope_width_m=stope.stope_width_m,
            equivalent_span_m=equivalent_stable_span,
        )

        cave_strike_length = calculate_stable_strike_length(
            surface_type=surface.surface_type,
            surface_angle_deg=surface.dip_deg,
            crown_angle_deg=crown_angle,
            stope_height_m=stope.stope_height_m,
            stope_width_m=stope.stope_width_m,
            equivalent_span_m=equivalent_caving_span,
        )

        effective_length_endwall = (
            stope.stope_height_m / _safe_sin_deg(hanging_wall_angle)
        ) / _safe_sin_deg(end_wall_angle)

        if surface.surface_type == SurfaceType.END_WALL:
            rating_length = effective_length_endwall
        else:
            rating_length = stope.stope_span_m

        state = classify_by_length(
            rating_length_m=rating_length,
            stable_length_m=stable_strike_length,
            cave_length_m=cave_strike_length,
        )

        actual_hr = calculate_surface_hydraulic_radius(
            surface_type=surface.surface_type,
            stope=stope,
        )

        local_state = None
        local_boundary_name = None
        local_boundary_n = None

        if calculation_mode == "Compare":
            local_state, local_boundary_name, local_boundary_n = assess_surface_local(
            project=stope.project_name,
            domain=stope.domain_name,
            surface=surface.surface_type.value,
            stability_number_n=stability_number_n,
            hydraulic_radius=actual_hr,
            db_path=db_path,
        )


        surface_results.append(
            SurfaceResult(
                surface_type=surface.surface_type,
                dip_deg=surface.dip_deg,
                q_prime=surface.q_prime,
                stress_factor_a=stress_factor_a,
                joint_factor_b=joint_factor_b,
                surface_factor_c=surface_factor_c,
                stability_number_n=stability_number_n,
                hr_stable=hr_stable,
                hr_caving=hr_caving,
                equivalent_stable_span=equivalent_stable_span,
                equivalent_caving_span=equivalent_caving_span,
                stable_strike_length_m=stable_strike_length,
                cave_strike_length_m=cave_strike_length,
                rating_length_m=rating_length,
                stability_state=state,
                actual_hr_m=actual_hr,
                local_state=local_state,
                local_boundary_name=local_boundary_name,
                local_boundary_n=local_boundary_n,
            )
        )

    final_state = get_worst_state([result.stability_state for result in surface_results])

    priority = {
        StabilityState.UNKNOWN: 0,
        StabilityState.STABLE: 1,
        StabilityState.UNSTABLE: 2,
        StabilityState.CAVED: 3,
    }

    limiting_surface_result = max(
        surface_results,
        key=lambda result: (
            priority[result.stability_state],
            result.rating_length_m / max(result.stable_strike_length_m, 0.0001),
        ),
    )

    local_final_state = None

    if calculation_mode in ("Local", "Compare"):
        local_states = [
            result.local_state
            for result in surface_results
            if result.local_state is not None
        ]

        if local_states:
            local_final_state = get_worst_state(local_states)

    return StopeResult(
        stope=stope,
        surfaces=surface_results,
        limiting_surface=limiting_surface_result.surface_type,
        final_state=final_state,
        calculation_mode=calculation_mode,
        local_final_state=local_final_state,
    )
