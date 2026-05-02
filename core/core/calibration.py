def apply_site_factor_to_stability_number(
    stability_number_n: float,
    site_factor: float,
) -> float:
    """
    Apply a simple site-specific correction factor.

    If site_factor > 1.0, the result becomes more conservative.
    """
    if stability_number_n <= 0:
        raise ValueError("Stability number must be greater than zero.")
    if site_factor <= 0:
        raise ValueError("Site factor must be greater than zero.")

    return stability_number_n / site_factor
