from dataclasses import dataclass
from enum import Enum


class SurfaceType(str, Enum):
    CROWN = "crown"
    HANGING_WALL = "hanging_wall"
    FOOTWALL = "footwall"
    END_WALL = "end_wall"


class StabilityState(str, Enum):
    STABLE = "stable"
    MINOR_FAILURE = "minor_failure"
    MAJOR_FAILURE = "major_failure"
    CAVED = "caved"
    UNKNOWN = "unknown"


@dataclass
class StopeSurfaceInput:
    surface_type: SurfaceType
    height_m: float
    length_m: float
    q_prime: float
    stress_factor_a: float
    orientation_factor_b: float
    gravity_factor_c: float


@dataclass
class StopeSurfaceResult:
    surface_type: SurfaceType
    hydraulic_radius_m: float
    stability_number_n: float
    predicted_state: StabilityState


