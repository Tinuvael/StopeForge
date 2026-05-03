import pytest

from core.mathews_factors import (
    calculate_surface_orientation_factor_c,
    calculate_true_interplane_angle_deg,
    calculate_b_from_true_interplane_angle,
    calculate_joint_orientation_factor_b,
)
from core.models import JointSet


def test_c_factor_uses_stopeforge_formula():
    assert calculate_surface_orientation_factor_c(0) == pytest.approx(2.0)
    assert calculate_surface_orientation_factor_c(90) == pytest.approx(8.0)

    # Important StopeForge rule:
    # C = 8 - 6 * cos(dip)
    assert calculate_surface_orientation_factor_c(60) == pytest.approx(5.0)


def test_true_interplane_angle_parallel_planes():
    angle = calculate_true_interplane_angle_deg(
        plane_1_dip_deg=90,
        plane_1_dip_direction_deg=90,
        plane_2_dip_deg=90,
        plane_2_dip_direction_deg=90,
    )

    assert angle == pytest.approx(0.0)


def test_true_interplane_angle_perpendicular_vertical_planes():
    angle = calculate_true_interplane_angle_deg(
        plane_1_dip_deg=90,
        plane_1_dip_direction_deg=90,
        plane_2_dip_deg=90,
        plane_2_dip_direction_deg=180,
    )

    assert angle == pytest.approx(90.0)


def test_b_factor_from_true_interplane_angle():
    assert calculate_b_from_true_interplane_angle(0) == pytest.approx(0.3)
    assert calculate_b_from_true_interplane_angle(20) == pytest.approx(0.2)
    assert calculate_b_from_true_interplane_angle(60) == pytest.approx(0.8)
    assert calculate_b_from_true_interplane_angle(90) == pytest.approx(1.0)


def test_joint_orientation_factor_b_uses_worst_joint_set():
    joint_sets = [
        JointSet(name="Good set", dip_deg=90, dip_direction_deg=180),  # B около 1
        JointSet(name="Bad set", dip_deg=90, dip_direction_deg=100),   # малый угол, B около 0.2
    ]

    b = calculate_joint_orientation_factor_b(
        surface_dip_deg=90,
        surface_dip_direction_deg=90,
        joint_sets=joint_sets,
    )

    assert b == pytest.approx(0.2, abs=0.15)


def test_joint_orientation_factor_b_without_joint_sets_is_neutral():
    b = calculate_joint_orientation_factor_b(
        surface_dip_deg=90,
        surface_dip_direction_deg=90,
        joint_sets=[],
    )

    assert b == pytest.approx(1.0)
