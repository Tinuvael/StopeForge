import math
import pytest
from core.models import JointSet, StabilityState, StopeInput, SurfaceInput, SurfaceType
from core.stability import calculate_hr_caving, calculate_hr_stable, calculate_stability_number_n, calculate_stope_result, classify_stability, get_surface_dip_direction

def make_stope():
    return StopeInput('Demo', 'Domain 1', 'S-01', 1000, 2.7, 120, 1.4, 75, 80, 25, 30, 90)

def test_stability_number_formula():
    assert calculate_stability_number_n(85, 0.1, 0.5, 1.0) == pytest.approx(4.25)

def test_hr_boundary_functions_are_stable_at_known_values():
    assert calculate_hr_stable(4.25) == pytest.approx(2.67 + 0.33 * 4.25)
    assert calculate_hr_caving(4.25) == pytest.approx(4.73 + 0.36 * 4.25)

def test_classify_stability_by_actual_hr_against_boundaries():
    assert classify_stability(3, 4, 8) == StabilityState.STABLE
    assert classify_stability(5, 4, 8) == StabilityState.UNSTABLE
    assert classify_stability(9, 4, 8) == StabilityState.CAVED

def test_surface_dip_directions_are_derived_from_hanging_wall_direction():
    stope = make_stope()
    assert get_surface_dip_direction(stope, SurfaceType.CROWN) == pytest.approx(90)
    assert get_surface_dip_direction(stope, SurfaceType.HANGING_WALL) == pytest.approx(90)
    assert get_surface_dip_direction(stope, SurfaceType.FOOTWALL) == pytest.approx(270)
    assert get_surface_dip_direction(stope, SurfaceType.END_WALL) == pytest.approx(0)

def test_calculate_stope_result_returns_four_surfaces_and_limiting_state():
    stope = make_stope()
    surfaces = [
        SurfaceInput(SurfaceType.CROWN, 0, 85),
        SurfaceInput(SurfaceType.HANGING_WALL, 80, 85),
        SurfaceInput(SurfaceType.FOOTWALL, 90, 85),
        SurfaceInput(SurfaceType.END_WALL, 90, 85),
    ]
    result = calculate_stope_result(stope, surfaces, [JointSet('flat', 0, 90)])
    assert len(result.surfaces) == 4
    crown = next(s for s in result.surfaces if s.surface_type == SurfaceType.CROWN)
    assert crown.stability_number_n == pytest.approx(85 * crown.stress_factor_a * crown.joint_factor_b * crown.surface_factor_c)
    assert crown.joint_factor_b == pytest.approx(0.3)
    assert crown.surface_factor_c == pytest.approx(1.0)
    assert crown.rating_length_m == pytest.approx(750 / 110)
    assert result.final_state in {StabilityState.STABLE, StabilityState.UNSTABLE, StabilityState.CAVED}
    assert math.isfinite(crown.hr_stable)
    assert crown.hr_caving > crown.hr_stable

def test_calculate_stope_result_rejects_empty_surface_list():
    with pytest.raises(ValueError):
        calculate_stope_result(make_stope(), [], [])
