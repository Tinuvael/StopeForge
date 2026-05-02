import pytest

from core.local_assessment import calculate_boundary_n


def test_linear_boundary_n():
    boundary = {
        "mode": "linear",
        "slope": 2.0,
        "intercept": 1.0,
    }

    assert calculate_boundary_n(3.0, boundary) == pytest.approx(7.0)


def test_power_boundary_n():
    boundary = {
        "mode": "power",
        "slope": 2.0,
        "intercept": 3.0,
    }

    # N = 3 * HR^2 = 3 * 4^2 = 48
    assert calculate_boundary_n(4.0, boundary) == pytest.approx(48.0)


def test_power_boundary_requires_positive_k():
    boundary = {
        "mode": "power",
        "slope": 2.0,
        "intercept": 0.0,
    }

    with pytest.raises(ValueError):
        calculate_boundary_n(4.0, boundary)
