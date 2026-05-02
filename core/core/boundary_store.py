from pathlib import Path
from typing import Any

from db.connection import get_connection, DEFAULT_PROJECT_DB_PATH
from db.schema import initialize_database



BOUNDARY_FIELDS = [
    "project",
    "domain",
    "surface",
    "boundary_name",
    "boundary_type",
    "mode",
    "slope",
    "intercept",
    "percentile",
    "margin",
    "is_standard",
    "is_active",
    "comment",
]



DEFAULT_BOUNDARIES_PATH = Path("data/boundaries/local_boundaries.csv")


def ensure_boundaries_file(path: str | Path = DEFAULT_BOUNDARIES_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=BOUNDARY_FIELDS)
            writer.writeheader()

    return path


def load_boundaries(path: str | Path = DEFAULT_BOUNDARIES_PATH) -> list[dict]:
    path = ensure_boundaries_file(path)

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return [{field: row.get(field, "") for field in BOUNDARY_FIELDS} for row in reader]


def save_boundaries(rows: list[dict], path: str | Path = DEFAULT_BOUNDARIES_PATH) -> None:
    path = ensure_boundaries_file(path)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=BOUNDARY_FIELDS)
        writer.writeheader()

        for row in rows:
            writer.writerow({field: row.get(field, "") for field in BOUNDARY_FIELDS})


def make_boundary_key(row: dict) -> tuple[str, str, str, str]:
    return (
        row.get("project", ""),
        row.get("domain", ""),
        row.get("surface", ""),
        row.get("boundary_name", ""),
    )


def upsert_boundary(new_row: dict, path: str | Path = DEFAULT_BOUNDARIES_PATH) -> None:
    rows = load_boundaries(path)
    new_key = make_boundary_key(new_row)

    updated = False

    for index, row in enumerate(rows):
        if make_boundary_key(row) == new_key:
            rows[index] = {field: new_row.get(field, "") for field in BOUNDARY_FIELDS}
            updated = True
            break

    if not updated:
        rows.append({field: new_row.get(field, "") for field in BOUNDARY_FIELDS})

    save_boundaries(rows, path)


def delete_boundary(target_row: dict, path: str | Path = DEFAULT_BOUNDARIES_PATH) -> None:
    rows = load_boundaries(path)
    target_key = make_boundary_key(target_row)

    rows = [row for row in rows if make_boundary_key(row) != target_key]

    save_boundaries(rows, path)

def list_boundaries_exact(
    project: str,
    domain: str,
    surface: str,
    boundary_type: str = "Stable-Unstable",
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    """
    List boundaries only for exact Project + Domain + Surface match.
    No wildcard matching.
    """
    initialize_database(db_path)

    query = """
        SELECT *
        FROM local_boundaries
        WHERE project = ?
          AND domain = ?
          AND surface = ?
          AND boundary_type = ?
    """
    params: list[Any] = [project, domain, surface, boundary_type]

    if active_only:
        query += " AND is_active = 1"

    query += """
        ORDER BY
            is_active DESC,
            boundary_name,
            id
    """

    with get_connection(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def find_active_boundary_exact(
    project: str,
    domain: str,
    surface: str,
    boundary_type: str = "Stable-Unstable",
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> dict[str, Any] | None:
    """
    Find active boundary only for exact Project + Domain + Surface match.
    """
    rows = list_boundaries_exact(
        project=project,
        domain=domain,
        surface=surface,
        boundary_type=boundary_type,
        db_path=db_path,
        active_only=True,
    )

    return rows[0] if rows else None


def set_active_boundary(
    boundary_id: int,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> None:
    """
    Make selected boundary active and deactivate other boundaries
    for the same Project + Domain + Surface + Boundary type.
    """
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        selected = connection.execute(
            """
            SELECT project, domain, surface, boundary_type
            FROM local_boundaries
            WHERE id = ?;
            """,
            (boundary_id,),
        ).fetchone()

        if selected is None:
            raise ValueError(f"Boundary id not found: {boundary_id}")

        connection.execute(
            """
            UPDATE local_boundaries
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE project = ?
              AND domain = ?
              AND surface = ?
              AND boundary_type = ?;
            """,
            (
                selected["project"],
                selected["domain"],
                selected["surface"],
                selected["boundary_type"],
            ),
        )

        connection.execute(
            """
            UPDATE local_boundaries
            SET is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (boundary_id,),
        )

        connection.commit()


def deactivate_boundary(
    boundary_id: int,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE local_boundaries
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (boundary_id,),
        )
        connection.commit()
