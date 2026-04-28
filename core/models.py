from dataclasses import dataclass
from enum import Enum


class SurfaceType(str, Enum):
    CROWN = "Crown"
    HANGING_WALL = "Hanging wall"
    FOOTWALL = "Footwall"
    END_WALL = "End wall"


class StabilityState(str, Enum):
    STABLE = "Stable"
    UNSTABLE = "Unstable"
    CAVED = "Caved"
    UNKNOWN = "Unknown"


@dataclass
class StopeInput:
    project_name: str
    domain_name: str
    stope_id: str

    depth_m: float
    unit_weight_t_m3: float
    ucs_mpa: float
    horizontal_stress_ratio: float

    stope_height_m: float
    average_dip_deg: float
    stope_width_m: float
    stope_span_m: float
    hanging_wall_dip_direction_deg: float


@dataclass
class JointSet:
    name: str
    dip_deg: float
    dip_direction_deg: float


@dataclass
class SurfaceInput:
    surface_type: SurfaceType
    dip_deg: float
    q_prime: float


@dataclass
class SurfaceResult:
    surface_type: SurfaceType
    dip_deg: float
    q_prime: float

    stress_factor_a: float
    joint_factor_b: float
    surface_factor_c: float
    stability_number_n: float

    hr_stable: float
    hr_caving: float
    equivalent_stable_span: float
    equivalent_caving_span: float

    stable_strike_length_m: float
    cave_strike_length_m: float
    rating_length_m: float

    stability_state: StabilityState


@dataclass
class StopeResult:
    stope: StopeInput
    surfaces: list[SurfaceResult]
    limiting_surface: SurfaceType
    final_state: StabilityState
