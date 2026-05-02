import pytest

from core.models import (
    JointSet,
    StopeInput,
    SurfaceInput,
    SurfaceType,
    StabilityState,
)
from core.stability import calculate_stope_result
from db.boundary_repository import upsert_boundary


def make_stope(project="Mayskoe", domain="Рудная зона 2"):
    return StopeInput(
        project_name=project,
        domain_name=domain,
        stope_id="Test-001",
        depth_m=500,
        unit_weight_t_m3=2.7,
        ucs_mpa=60,
        horizontal_stress_ratio=1.2,
        stope_height_m=20,
        average_dip_deg=80,
        stope_width_m=4,
        stope_span_m=12,
        hanging_wall_dip_direction_deg=90,
    )


def make_surfaces():
    return [
        SurfaceInput(
            surface_type=SurfaceType.CROWN,
            dip_deg=0,
            q_prime=10,
        ),
        SurfaceInput(
            surface_type=SurfaceType.HANGING_WALL,
            dip_deg=80,
            q_prime=10,
        ),
        SurfaceInput(
            surface_type=SurfaceType.FOOTWALL,
            dip_deg=80,
            q_prime=10,
        ),
        SurfaceInput(
            surface_type=SurfaceType.END_WALL,
            dip_deg=90,
            q_prime=10,
        ),
    ]


def make_joint_sets():
    return [
        JointSet(
            name="Set 1",
            dip_deg=70,
            dip_direction_deg=100,
        )
    ]


def test_standard_calculation_returns_four_surfaces():
    result = calculate_stope_result(
        stope=make_stope(),
        surfaces=make_surfaces(),
        joint_sets=make_joint_sets(),
        calculation_mode="Standard",
    )

    assert len(result.surfaces) == 4
    assert result.calculation_mode == "Standard"
    assert result.final_state in (
        StabilityState.STABLE,
        StabilityState.UNSTABLE,
        StabilityState.CAVED,
        StabilityState.UNKNOWN,
    )

    for surface in result.surfaces:
        assert surface.stability_number_n > 0
        assert surface.hr_stable > 0
        assert surface.hr_caving > 0
        assert surface.actual_hr_m is not None
        assert surface.local_state is None
        assert surface.local_boundary_name is None
        assert surface.local_boundary_n is None


def test_a_override_is_used():
    surfaces = make_surfaces()
    surfaces[0] = SurfaceInput(
        surface_type=SurfaceType.CROWN,
        dip_deg=0,
        q_prime=10,
        stress_factor_a=0.5,
    )

    result = calculate_stope_result(
        stope=make_stope(),
        surfaces=surfaces,
        joint_sets=make_joint_sets(),
        calculation_mode="Standard",
    )

    crown = next(
        surface
        for surface in result.surfaces
        if surface.surface_type == SurfaceType.CROWN
    )

    assert crown.stress_factor_a == pytest.approx(0.5)


def test_compare_mode_uses_saved_local_boundary(monkeypatch, tmp_path):
    # SQLite база будет создаваться во временной папке теста,
    # а не в рабочем data/projects проекта.
    monkeypatch.chdir(tmp_path)

    upsert_boundary(
        {
            "project": "Mayskoe",
            "domain": "Рудная зона 2",
            "surface": "Hanging wall",
            "boundary_name": "Test HW boundary",
            "boundary_type": "Stable-Unstable",
            "mode": "linear",
            "slope": 0.1,
            "intercept": 0.1,
            "percentile": 80,
            "margin": 0,
            "is_standard": 0,
            "is_active": 1,
            "comment": "pytest boundary",
        }
    )

    result = calculate_stope_result(
        stope=make_stope(project="Mayskoe", domain="Рудная зона 2"),
        surfaces=make_surfaces(),
        joint_sets=make_joint_sets(),
        calculation_mode="Compare",
    )

    hanging_wall = next(
        surface
        for surface in result.surfaces
        if surface.surface_type == SurfaceType.HANGING_WALL
    )

    assert result.calculation_mode == "Compare"
    assert hanging_wall.local_boundary_name == "Test HW boundary"
    assert hanging_wall.local_boundary_n is not None
    assert hanging_wall.local_state in (
        StabilityState.STABLE,
        StabilityState.UNSTABLE,
        StabilityState.UNKNOWN,
    )


def test_compare_mode_without_boundary_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = calculate_stope_result(
        stope=make_stope(project="No project", domain="No domain"),
        surfaces=make_surfaces(),
        joint_sets=make_joint_sets(),
        calculation_mode="Compare",
    )

    assert result.calculation_mode == "Compare"

    for surface in result.surfaces:
        assert surface.local_state == StabilityState.UNKNOWN
        assert surface.local_boundary_name == "Not found"
