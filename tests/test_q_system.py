import pytest
from core.q_system import calculate_q_prime

def test_calculate_q_prime_uses_modified_ngi_q_formula():
    assert calculate_q_prime(85, 3, 3, 1) == pytest.approx(85.0)

@pytest.mark.parametrize('args', [(0,3,3,1),(85,0,3,1),(85,3,0,1),(85,3,3,0)])
def test_calculate_q_prime_rejects_zero_or_negative_inputs(args):
    with pytest.raises(ValueError):
        calculate_q_prime(*args)
