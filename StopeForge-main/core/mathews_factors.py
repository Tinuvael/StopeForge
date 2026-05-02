import math

from core.models import JointSet


def calculate_f1(delta_dip: float) -> float:
    if 0 <= delta_dip <= 10:
        return 0.3 - 0.01 * delta_dip
    if 10 < delta_dip <= 30:
        return 0.2
    if 30 < delta_dip <= 60:
        return -0.4 + 0.02 * delta_dip
    if 60 < delta_dip <= 90:
        return 0.4 + 0.00666 * delta_dip
    return 0.0


def calculate_f2(delta_dip: float) -> float:
    if 0 <= delta_dip <= 10:
        return 0.3 - 0.01 * delta_dip
    if 10 < delta_dip <= 30:
        return 0.1 + 0.01 * delta_dip
    if 30 < delta_dip <= 45:
        return 0.0133 * delta_dip
    if 45 < delta_dip <= 60:
        return -0.09 + 0.0153 * delta_dip
    if 60 < delta_dip <= 75:
        return 0.55 + 0.0047 * delta_dip
    if 75 < delta_dip <= 90:
        return 0.4 + 0.00666 * delta_dip
    return 0.0


def calculate_f3(delta_dip: float) -> float:
    if 0 <= delta_dip <= 10:
        return 0.5
    if 10 < delta_dip <= 30:
        return 0.45 + 0.005 * delta_dip
    if 30 < delta_dip <= 45:
        return 0.2 + 0.0133 * delta_dip
    if 45 < delta_dip <= 90:
        return 0.6 + 0.0044 * delta_dip
    return 0.0


def calculate_f4(delta_dip: float) -> float:
    if 0 <= delta_dip <= 10:
        return 0.8
    if 10 < delta_dip <= 45:
        return 0.7857 + 0.0014 * delta_dip
    if 45 < delta_dip <= 90:
        return 0.7 + 0.0033 * delta_dip
    return 0.0


def calculate_b_intermediate(delta_az: float, delta_dip: float) -> float:
    f0 = calculate_f1(delta_dip)
    f30 = calculate_f2(delta_dip)
    f45 = calculate_f3(delta_dip)
    f60 = calculate_f4(delta_dip)
    f90 = 1.0

    if 0 <= delta_az <= 30:
        return f0 + (f30 - f0) * delta_az / 30
    if 30 < delta_az <= 45:
        return f30 + (f45 - f30) * (delta_az - 30) / 15
    if 45 < delta_az <= 60:
        return f45 + (f60 - f45) * (delta_az - 45) / 15
    if 60 < delta_az <= 90:
        return f60 + (f90 - f60) * (delta_az - 60) / 30

    return 0.0


def calculate_delta_dip(
    joint_dip_deg: float,
    surface_dip_deg: float,
    delta_az_raw_deg: float,
) -> float:
    if delta_az_raw_deg <= 90 or 270 <= delta_az_raw_deg <= 360:
        return abs(joint_dip_deg - surface_dip_deg)

    option_1 = abs(180 - (joint_dip_deg + surface_dip_deg))
    option_2 = abs(joint_dip_deg + surface_dip_deg)

    return min(option_1, option_2)


def calculate_joint_orientation_factor_b(
    surface_dip_deg: float,
    surface_dip_direction_deg: float,
    joint_sets: list,
) -> float:
    """
    Calculate B using true interplane angle between stope surface
    and each joint set. The lowest B is critical.
    """
    b_values = []

    for joint_set in joint_sets:
        true_angle = calculate_true_interplane_angle_deg(
            plane_1_dip_deg=surface_dip_deg,
            plane_1_dip_direction_deg=surface_dip_direction_deg,
            plane_2_dip_deg=joint_set.dip_deg,
            plane_2_dip_direction_deg=joint_set.dip_direction_deg,
        )

        b_values.append(calculate_b_from_true_interplane_angle(true_angle))

    if not b_values:
        return 1.0

    return min(b_values)


def calculate_stress_factor_a(
    depth_m: float,
    unit_weight_t_m3: float,
    ucs_mpa: float,
) -> float:
    """
    Calculate rock stress factor A.

    This uses the simplified approach from the previous FjordUG prototype.

    vertical_stress_mpa = unit_weight_t_m3 * 0.01 * depth_m

    ratio = UCS / vertical_stress

    A:
    - 0.1 when ratio < 2.25
    - linear interpolation when 2.25 <= ratio < 10
    - 1.0 when ratio >= 10
    """
    if depth_m <= 0:
        raise ValueError("Depth must be greater than zero.")
    if unit_weight_t_m3 <= 0:
        raise ValueError("Unit weight must be greater than zero.")
    if ucs_mpa <= 0:
        raise ValueError("UCS must be greater than zero.")

    vertical_stress_mpa = unit_weight_t_m3 * 0.01 * depth_m

    if vertical_stress_mpa <= 0:
        raise ValueError("Vertical stress must be greater than zero.")

    ratio = ucs_mpa / vertical_stress_mpa

    if ratio < 2.25:
        return 0.1
    if ratio < 10:
        return 0.1161 * ratio - 0.1613

    return 1.0


def calculate_surface_orientation_factor_c(dip_from_horizontal_deg: float) -> float:
    """
    Calculate surface orientation factor C.

    Current implementation uses the formula from the previous FjordUG prototype:

    C = 8 - 6 * cos(dip)

    where dip is measured from horizontal.

    Note:
    Some references use C = 8 - 7 * cos(dip). We will keep this explicit
    and make it configurable later if needed.
    """
    if dip_from_horizontal_deg < 0 or dip_from_horizontal_deg > 90:
        raise ValueError("Surface dip must be between 0 and 90 degrees.")

    return 8 - 6 * math.cos(math.radians(dip_from_horizontal_deg))


def calculate_true_interplane_angle_deg(
    plane_1_dip_deg: float,
    plane_1_dip_direction_deg: float,
    plane_2_dip_deg: float,
    plane_2_dip_direction_deg: float,
) -> float:
    """
    True interplane angle between two planes using their poles.

    Input:
    - dip and dip direction for plane 1
    - dip and dip direction for plane 2

    Output:
    - smallest angle between the two planes, degrees, range 0–90
    """

    def pole_vector(dip_deg: float, dip_direction_deg: float):
        trend_deg = (dip_direction_deg + 180.0) % 360.0
        plunge_deg = 90.0 - dip_deg

        trend_rad = math.radians(trend_deg)
        plunge_rad = math.radians(plunge_deg)

        north = math.cos(trend_rad) * math.cos(plunge_rad)
        east = math.sin(trend_rad) * math.cos(plunge_rad)
        down = math.sin(plunge_rad)

        return north, east, down

    n1, e1, d1 = pole_vector(plane_1_dip_deg, plane_1_dip_direction_deg)
    n2, e2, d2 = pole_vector(plane_2_dip_deg, plane_2_dip_direction_deg)

    dot_product = n1 * n2 + e1 * e2 + d1 * d2

    # Plane poles can be opposite while describing the same plane.
    # abs() gives the smallest angle between planes.
    dot_product = abs(dot_product)
    dot_product = max(-1.0, min(1.0, dot_product))

    return math.degrees(math.acos(dot_product))


def calculate_b_from_true_interplane_angle(angle_deg: float) -> float:
    """
    Approximation of Potvin B factor from true interplane angle.

    Worst orientation is shallow-oblique, around 10–30 degrees.
    Perpendicular joints approach B = 1.0.
    """
    if angle_deg < 0 or angle_deg > 90:
        raise ValueError("True interplane angle must be between 0 and 90 degrees.")

    if angle_deg <= 10:
        return 0.3 - 0.01 * angle_deg

    if angle_deg <= 30:
        return 0.2

    if angle_deg <= 60:
        return -0.4 + 0.02 * angle_deg

    return 0.4 + angle_deg / 150.0
