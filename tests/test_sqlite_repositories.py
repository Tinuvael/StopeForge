from db.schema import initialize_database
from db.case_repository import (
    create_case,
    list_cases,
    update_case,
    delete_case,
)
from db.boundary_repository import (
    upsert_boundary,
    list_boundaries,
    find_best_boundary,
    delete_boundary,
)


def test_case_repository_create_list_update_delete(tmp_path):
    db_path = tmp_path / "test_project.sqlite"

    initialize_database(db_path)

    case_id = create_case(
        {
            "project": "Mayskoe",
            "domain": "Рудная зона 2",
            "stope_id": "Test-001",
            "surface": "Hanging wall",
            "q_prime": 10,
            "a": 0.5,
            "b": 0.8,
            "c": 7.0,
            "n": 28.0,
            "shape_factor_hr_m": 2.5,
            "predicted_state": "Stable",
            "calculation_mode": "Standard",
            "standard_state": "Stable",
            "observed_state": "Unknown",
            "comment": "Initial comment",
        },
        db_path=db_path,
    )

    rows = list_cases(db_path=db_path, project="Mayskoe")

    assert len(rows) == 1
    assert rows[0]["id"] == case_id
    assert rows[0]["project"] == "Mayskoe"
    assert rows[0]["observed_state"] == "Unknown"

    update_case(
        case_id,
        {
            "observed_state": "Unstable",
            "comment": "Updated comment",
        },
        db_path=db_path,
    )

    rows = list_cases(db_path=db_path, project="Mayskoe")

    assert rows[0]["observed_state"] == "Unstable"
    assert rows[0]["comment"] == "Updated comment"

    delete_case(case_id, db_path=db_path)

    rows = list_cases(db_path=db_path, project="Mayskoe")

    assert rows == []


def test_boundary_repository_upsert_list_find_delete(tmp_path):
    db_path = tmp_path / "test_project.sqlite"

    initialize_database(db_path)

    wildcard_id = upsert_boundary(
        {
            "project": "Mayskoe",
            "domain": "",
            "surface": "",
            "boundary_name": "Wildcard boundary",
            "boundary_type": "Stable-Unstable",
            "mode": "linear",
            "slope": 0.5,
            "intercept": -0.8,
            "is_active": 1,
        },
        db_path=db_path,
    )

    exact_id = upsert_boundary(
        {
            "project": "Mayskoe",
            "domain": "Рудная зона 2",
            "surface": "Hanging wall",
            "boundary_name": "Exact boundary",
            "boundary_type": "Stable-Unstable",
            "mode": "linear",
            "slope": 0.8,
            "intercept": -1.2,
            "is_active": 1,
        },
        db_path=db_path,
    )

    rows = list_boundaries(db_path=db_path, project="Mayskoe")

    assert len(rows) == 2

    best = find_best_boundary(
        project="Mayskoe",
        domain="Рудная зона 2",
        surface="Hanging wall",
        db_path=db_path,
    )

    assert best is not None
    assert best["boundary_name"] == "Exact boundary"

    # Проверяем upsert: та же уникальная комбинация должна обновиться.
    upsert_boundary(
        {
            "project": "Mayskoe",
            "domain": "Рудная зона 2",
            "surface": "Hanging wall",
            "boundary_name": "Exact boundary",
            "boundary_type": "Stable-Unstable",
            "mode": "linear",
            "slope": 1.2,
            "intercept": -2.0,
            "is_active": 1,
        },
        db_path=db_path,
    )

    best = find_best_boundary(
        project="Mayskoe",
        domain="Рудная зона 2",
        surface="Hanging wall",
        db_path=db_path,
    )

    assert best["slope"] == 1.2
    assert best["intercept"] == -2.0

    delete_boundary(exact_id, db_path=db_path)

    best = find_best_boundary(
        project="Mayskoe",
        domain="Рудная зона 2",
        surface="Hanging wall",
        db_path=db_path,
    )

    assert best is not None
    assert best["boundary_name"] == "Wildcard boundary"

    delete_boundary(wildcard_id, db_path=db_path)

    rows = list_boundaries(db_path=db_path, project="Mayskoe")
    assert rows == []
