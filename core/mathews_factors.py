def calculate_surface_orientation_factor_c(
    dip_from_horizontal_deg: float,
) -> float:
    """
    Calculate Mathews surface orientation factor C.

    Basic formula often used:

    C = 8 - 7 * cos(dip)

    where dip is measured from horizontal.

    This function is a starting implementation and should be verified
    against the selected Mathews–Potvin reference curves.
    """
    import math

    if dip_from_horizontal_deg < 0 or dip_from_horizontal_deg > 90:
        raise ValueError("Dip from horizontal must be between 0 and 90 degrees.")

    dip_rad = math.radians(dip_from_horizontal_deg)

    return 8 - 7 * math.cos(dip_rad)

