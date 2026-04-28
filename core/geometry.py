def calculate_area(height_m: float, length_m: float) -> float:
    """
    Calculate rectangular stope surface area.

    Parameters
    ----------
    height_m : float
        Surface height in metres.
    length_m : float
        Surface length in metres.

    Returns
    -------
    float
        Area in square metres.
    """
    if height_m <= 0 or length_m <= 0:
        raise ValueError("Height and length must be greater than zero.")

    return height_m * length_m


def calculate_perimeter(height_m: float, length_m: float) -> float:
    """
    Calculate rectangular stope surface perimeter.
    """
    if height_m <= 0 or length_m <= 0:
        raise ValueError("Height and length must be greater than zero.")

    return 2 * (height_m + length_m)


def calculate_hydraulic_radius(height_m: float, length_m: float) -> float:
    """
    Calculate hydraulic radius:

    HR = Area / Perimeter
    """
    area = calculate_area(height_m, length_m)
    perimeter = calculate_perimeter(height_m, length_m)

    return area / perimeter

