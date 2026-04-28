from core.geometry import calculate_surface_hydraulic_radius
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
    """
    Stable hydraulic radius limit.

    Transferred from the previous FjordUG prototype.
    """
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
    """
    Caving / major failure hydraulic radius limit.

    Transferred from the previous FjordUG prototype.
    """
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


def classify_surface_stability(
    actual_hr: float,
    stable_hr_limit: float,
    caving_hr_limit: float,
) -> StabilityState:
    if actual_hr <= 0:
        return StabilityState.UNKNOWN

    if actual_hr <= stable_hr_limit:
        return StabilityState.STABLE

    if actual_hr <= caving_hr_limit:
        return StabilityState.TRANSITION

    return StabilityState.CAVED


def get_worst_state(states: list[StabilityState]) -> StabilityState:
    priority = {
        StabilityState.UNKNOWN: 0,
        StabilityState.STABLE: 1,
        StabilityState.TRANSITION: 2,
        StabilityState.CAVED: 3,
    }

    return max(states, key=lambda state: priority[state])


def calculate_stope_result(
    stope: StopeInput,
    surfaces: list[SurfaceInput],
    joint_sets: list[JointSet],
) -> StopeResult:
    stress_factor_a = calculate_stress_factor_a(
        depth_m=stope.depth_m,
        unit_weight_t_m3=stope.unit_weight_t_m3,
        ucs_mpa=stope.ucs_mpa,
    )

    surface_results: list[SurfaceResult] = []

    for surface in surfaces:
        joint_factor_b = calculate_joint_orientation_factor_b(
            surface_dip_deg=surface.dip_deg,
            surface_dip_direction_deg=surface.dip_direction_deg,
            joint_sets=joint_sets,
        )

        surface_factor_c = calculate_surface_orientation_factor_c(surface.dip_deg)

        stability_number_n = calculate_stability_number(
            q_prime=surface.q_prime,
            stress_factor_a=stress_factor_a,
            joint_factor_b=joint_factor_b,
            surface_factor_c=surface_factor_c,
        )

        actual_hr = calculate_surface_hydraulic_radius(
            surface_type=surface.surface_type,
            stope_height_m=stope.stope_height_m,
            stope_width_m=stope.stope_width_m,
            stope_span_m=stope.stope_span_m,
        )

        stable_hr_limit = calculate_stable_hr_limit(stability_number_n)
        caving_hr_limit = calculate_caving_hr_limit(stability_number_n)

        state = classify_surface_stability(
            actual_hr=actual_hr,
            stable_hr_limit=stable_hr_limit,
            caving_hr_limit=caving_hr_limit,
        )

        surface_results.append(
            SurfaceResult(
                surface_type=surface.surface_type,
                dip_deg=surface.dip_deg,
                dip_direction_deg=surface.dip_direction_deg,
                q_prime=surface.q_prime,
                stress_factor_a=stress_factor_a,
                joint_factor_b=joint_factor_b,
                surface_factor_c=surface_factor_c,
                stability_number_n=stability_number_n,
                actual_hydraulic_radius_m=actual_hr,
                stable_hydraulic_radius_limit_m=stable_hr_limit,
                caving_hydraulic_radius_limit_m=caving_hr_limit,
                stability_state=state,
            )
        )

    final_state = get_worst_state([result.stability_state for result in surface_results])

    limiting_surface_result = max(
        surface_results,
        key=lambda result: (
            {
                StabilityState.UNKNOWN: 0,
                StabilityState.STABLE: 1,
                StabilityState.TRANSITION: 2,
                StabilityState.CAVED: 3,
            }[result.stability_state],
            result.actual_hydraulic_radius_m / max(result.stable_hydraulic_radius_limit_m, 0.0001),
        ),
    )

    return StopeResult(
        stope=stope,
        surfaces=surface_results,
        limiting_surface=limiting_surface_result.surface_type,
        final_state=final_state,
    )
