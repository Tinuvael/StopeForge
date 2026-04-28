import pytest
from core.geometry import calculate_area, calculate_hydraulic_radius, calculate_perimeter, calculate_surface_hydraulic_radius
from core.models import SurfaceType

def test_area_perimeter_and_hydraulic_radius():
    assert calculate_area(75, 10) == pytest.approx(750)
    assert calculate_perimeter(75, 10) == pytest.approx(170)
    assert calculate_hydraulic_radius(75, 10) == pytest.approx(750 / 170)

def test_surface_hydraulic_radius_by_surface_type():
    assert calculate_surface_hydraulic_radius(SurfaceType.CROWN, 75, 25, 30) == pytest.approx(750 / 110)
    assert calculate_surface_hydraulic_radius(SurfaceType.HANGING_WALL, 75, 25, 30) == pytest.approx(2250 / 210)
    assert calculate_surface_hydraulic_radius(SurfaceType.FOOTWALL, 75, 25, 30) == pytest.approx(2250 / 210)
    assert calculate_surface_hydraulic_radius(SurfaceType.END_WALL, 75, 25, 30) == pytest.approx(1875 / 200)

@pytest.mark.parametrize('height,length', [(0,10),(10,0),(-1,10),(10,-1)])
def test_hydraulic_radius_rejects_invalid_dimensions(height, length):
    with pytest.raises(ValueError):
        calculate_hydraulic_radius(height, length)
