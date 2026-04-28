import pytest
from core.mathews_factors import calculate_joint_orientation_factor_b, calculate_stress_factor_a, calculate_surface_orientation_factor_c
from core.models import JointSet

def test_stress_factor_a_thresholds_and_interpolation():
    assert calculate_stress_factor_a(1000, 2.7, 50) == pytest.approx(0.1)
    assert calculate_stress_factor_a(1000, 2.7, 270) == pytest.approx(1.0)
    assert calculate_stress_factor_a(1000, 2.7, 120) == pytest.approx(0.3547, abs=1e-4)

def test_surface_orientation_factor_c_matches_mathews_reference_formula():
    assert calculate_surface_orientation_factor_c(0) == pytest.approx(1.0)
    assert calculate_surface_orientation_factor_c(90) == pytest.approx(8.0)
    assert calculate_surface_orientation_factor_c(80) == pytest.approx(8 - 7 * 0.1736481777)

@pytest.mark.parametrize('dip', [-1,91])
def test_surface_orientation_factor_rejects_invalid_dip(dip):
    with pytest.raises(ValueError):
        calculate_surface_orientation_factor_c(dip)

def test_joint_orientation_factor_uses_most_critical_joint_set():
    joint_sets = [JointSet('good', 80, 10), JointSet('critical', 0, 90)]
    assert calculate_joint_orientation_factor_b(0, 90, joint_sets) == pytest.approx(0.3)

def test_joint_orientation_factor_has_conservative_default_without_joint_sets():
    assert calculate_joint_orientation_factor_b(70, 120, []) == pytest.approx(0.2)
