from pathlib import Path
from typing import Any

from db.connection import get_connection, DEFAULT_PROJECT_DB_PATH
from db.schema import initialize_database


CASE_FIELDS = [
    "project",
    "domain",
    "stope_id",
    "surface",
    "depth_m",
    "height_m",
    "avg_dip_deg",
    "width_m",
    "span_m",
    "q_prime",
    "a",
    "b",
    "c",
    "n",
    "shape_factor_hr_m",
    "stable_hr_limit_m",
    "predicted_state",
    "calculation_mode",
    "standard_state",
    "local_state",
    "local_boundary_name",
    "local_boundary_n",
    "actual_hr_m",
    "observed_state",
    "comment",
]



def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    clean_row = {field: row.get(field, None) for field in CASE_FIELDS}

    # Text fields with NOT NULL constraints / sensible defaults
    text_defaults = {
        "project": "",
        "domain": "",
        "stope_id": "",
        "surface": "",
        "predicted_state": "",
        "calculation_mode": "Standard",
        "standard_state": "",
        "local_state": "",
        "local_boundary_name": "",
        "observed_state": "Unknown",
        "comment": "",
    }


    for field, default_value in text_defaults.items():
        if clean_row.get(field) is None:
            clean_row[field] = default_value

    return clean_row



def create_case(row: dict[str, Any], db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> int:
    initialize_database(db_path)

    clean_row = _normalize_row(row)

    columns = ", ".join(CASE_FIELDS)
    placeholders = ", ".join(["?"] * len(CASE_FIELDS))

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            f"""
            INSERT INTO case_histories ({columns})
            VALUES ({placeholders});
            """,
            [clean_row[field] for field in CASE_FIELDS],
        )
        connection.commit()
        return int(cursor.lastrowid)


def create_cases(rows: list[dict[str, Any]], db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> list[int]:
    initialize_database(db_path)

    inserted_ids = []

    for row in rows:
        inserted_ids.append(create_case(row, db_path))

    return inserted_ids


def list_cases(
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
    project: str | None = None,
    domain: str | None = None,
    surface: str | None = None,
    observed_state: str | None = None,
) -> list[dict[str, Any]]:
    initialize_database(db_path)

    query = "SELECT * FROM case_histories WHERE 1=1"
    params: list[Any] = []

    if project not in (None, "", "All"):
        query += " AND project = ?"
        params.append(project)

    if domain not in (None, "", "All"):
        query += " AND domain = ?"
        params.append(domain)

    if surface not in (None, "", "All"):
        query += " AND surface = ?"
        params.append(surface)

    if observed_state not in (None, "", "All"):
        query += " AND observed_state = ?"
        params.append(observed_state)

    query += " ORDER BY project, domain, stope_id, surface, id"

    with get_connection(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def update_case(case_id: int, values: dict[str, Any], db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> None:
    initialize_database(db_path)

    allowed_values = {
        key: value
        for key, value in values.items()
        if key in CASE_FIELDS
    }

    if not allowed_values:
        return

    set_clause = ", ".join([f"{key} = ?" for key in allowed_values])
    params = list(allowed_values.values())
    params.append(case_id)

    with get_connection(db_path) as connection:
        connection.execute(
            f"""
            UPDATE case_histories
            SET {set_clause},
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            params,
        )
        connection.commit()


def delete_case(case_id: int, db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            "DELETE FROM case_histories WHERE id = ?;",
            (case_id,),
        )
        connection.commit()


def delete_all_cases(db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute("DELETE FROM case_histories;")
        connection.commit()
