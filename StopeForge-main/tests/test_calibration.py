import pytest
from core.calibration import apply_site_factor_to_stability_number

def test_apply_site_factor_to_stability_number_is_conservative_when_factor_above_one():
    assert apply_site_factor_to_stability_number(20, 2) == pytest.approx(10)

@pytest.mark.parametrize('n,site_factor', [(0,1),(10,0),(-1,1),(10,-1)])
def test_apply_site_factor_rejects_invalid_values(n, site_factor):
    with pytest.raises(ValueError):
        apply_site_factor_to_stability_number(n, site_factor)
