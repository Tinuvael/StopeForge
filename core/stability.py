from core.models import StabilityState


def calculate_stability_number(
    q_prime: float,
    stress_factor_a: float,
    orientation_factor_b: float,
    gravity_factor_c: float,
) -> float:
    """
    Calculate Mathews stability number:

    N = Q' * A * B * C
    """
    values = {
        "Q'": q_prime,
        "A": stress_factor_a,
        "B": orientation_factor_b,
        "C": gravity_factor_c,
    }

    for name, value in values.items():
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    return q_prime * stress_factor_a * orientation_factor_b * gravity_factor_c


def classify_stability_placeholder(
    hydraulic_radius_m: float,
    stability_number_n: float,
) -> StabilityState:
    """
    Temporary placeholder classification.

    Real Mathews–Potvin empirical boundaries will be implemented later.
    """
    if hydraulic_radius_m <= 0 or stability_number_n <= 0:
        return StabilityState.UNKNOWN

    ratio = stability_number_n / hydraulic_radius_m

    if ratio >= 10:
        return StabilityState.STABLE
    if ratio >= 3:
        return StabilityState.MINOR_FAILURE
    if ratio >= 1:
        return StabilityState.MAJOR_FAILURE

    return StabilityState.CAVED

