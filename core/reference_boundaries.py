import numpy as np

ORIGINAL_STABLE_FAILURE = [
    (2.413965, 1.496236),
    (3.259512, 2.585235),
    (4.698811, 4.869675),
    (6.775225, 9.440609),
    (9.869090, 20.535250),
    (14.633946, 40.973211),
    (22.747188, 91.727594),
    (34.702555, 199.526231),
    (48.646118, 365.174127),
    (62.111596, 595.662144),
]

ORIGINAL_FAILURE_MAJOR = [
    (2.339248, 0.298538),
    (3.128827, 0.501187),
    (4.467869, 0.917276),
    (6.265965, 1.778279),
    (9.032819, 3.349654),
    (12.788727, 6.683439),
    (17.927266, 12.232071),
    (25.375679, 23.713737),
    (34.264102, 40.973211),
    (48.500138, 79.432823),
    (62.486059, 125.892541),
]

MODIFIED_STABLE_FAILURE = [
    (1.774144, 0.527588),
    (2.200352, 0.807990),
    (2.798882, 1.507100),
    (3.546757, 2.453311),
    (4.294631, 3.993588),
    (5.280309, 6.473450),
    (6.426821, 10.818273),
    (7.808838, 17.412734),
    (8.939266, 23.044333),
    (9.990427, 30.540350),
    (11.360956, 41.610994),
    (12.808455, 54.758869),
    (13.855020, 67.891336),
    (15.057823, 81.184636),
    (16.183656, 100.512721),
]

MODIFIED_FAILURE_MAJOR = [
    (3.730566, 0.352982),
    (4.238340, 0.558118),
    (4.753006, 0.975269),
    (5.580149, 1.585340),
    (6.241863, 2.338411),
    (7.386076, 3.779793),
    (8.691124, 6.298901),
    (9.588343, 8.948495),
    (10.716474, 11.454396),
    (11.853795, 16.753068),
    (12.818795, 20.118331),
    (13.627556, 25.048973),
]


def interpolate_boundary(points, samples=400):
    """
    Interpolate a boundary in log-log space.
    Returns:
        hr_values, n_values
    """

    pts = np.asarray(points, dtype=float)

    hr = pts[:, 0]
    n = pts[:, 1]

    log_hr = np.log10(hr)
    log_n = np.log10(n)

    x = np.linspace(log_hr.min(), log_hr.max(), samples)
    y = np.interp(x, log_hr, log_n)

    return 10 ** x, 10 ** y


REFERENCE_BOUNDARIES = {
    "Original Mathews–Potvin": (
        ORIGINAL_STABLE_FAILURE,
        ORIGINAL_FAILURE_MAJOR,
    ),
    "Modified Mathews Graph": (
        MODIFIED_STABLE_FAILURE,
        MODIFIED_FAILURE_MAJOR,
    ),
}


def get_reference_boundaries(name: str):
    stable, caved = REFERENCE_BOUNDARIES[name]

    stable_x, stable_y = interpolate_boundary(stable)
    caved_x, caved_y = interpolate_boundary(caved)

    return stable_x, stable_y, caved_x, caved_y
