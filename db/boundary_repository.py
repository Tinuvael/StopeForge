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


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    clean_row = {field: row.get(field, None) for field in BOUNDARY_FIELDS}

    text_defaults = {
        "project": "",
        "domain": "",
        "surface": "",
        "boundary_name": "",
        "boundary_type": "Stable-Unstable",
        "mode": "linear",
        "comment": "",
    }

    for field, default_value in text_defaults.items():
        if clean_row.get(field) in (None, ""):
            clean_row[field] = default_value

    if clean_row["is_standard"] in (None, ""):
        clean_row["is_standard"] = 0

    if clean_row["is_active"] in (None, ""):
        clean_row["is_active"] = 1

    return clean_row


def upsert_boundary(
    row: dict[str, Any],
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> int:
    initialize_database(db_path)

    clean_row = _normalize_row(row)

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO local_boundaries (
                project,
                domain,
                surface,
                boundary_name,
                boundary_type,
                mode,
                slope,
                intercept,
                percentile,
                margin,
                is_standard,
                is_active,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project, domain, surface, boundary_name, boundary_type)
            DO UPDATE SET
                mode = excluded.mode,
                slope = excluded.slope,
                intercept = excluded.intercept,
                percentile = excluded.percentile,
                margin = excluded.margin,
                is_standard = excluded.is_standard,
                is_active = excluded.is_active,
                comment = excluded.comment,
                updated_at = CURRENT_TIMESTAMP;
            """,
            [clean_row[field] for field in BOUNDARY_FIELDS],
        )

        connection.commit()

        if cursor.lastrowid:
            return int(cursor.lastrowid)

        existing = connection.execute(
            """
            SELECT id
            FROM local_boundaries
            WHERE project = ?
              AND domain = ?
              AND surface = ?
              AND boundary_name = ?
              AND boundary_type = ?;
            """,
            (
                clean_row["project"],
                clean_row["domain"],
                clean_row["surface"],
                clean_row["boundary_name"],
                clean_row["boundary_type"],
            ),
        ).fetchone()

        if existing is None:
            raise ValueError("Boundary was not inserted or found after upsert.")

        return int(existing["id"])


def list_boundaries(
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
    project: str | None = None,
    domain: str | None = None,
    surface: str | None = None,
    boundary_type: str | None = None,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    initialize_database(db_path)

    query = "SELECT * FROM local_boundaries WHERE 1=1"
    params: list[Any] = []

    if project not in (None, "", "All"):
        query += " AND (project = ? OR project = '')"
        params.append(project)

    if domain not in (None, "", "All"):
        query += " AND (domain = ? OR domain = '')"
        params.append(domain)

    if surface not in (None, "", "All"):
        query += " AND (surface = ? OR surface = '')"
        params.append(surface)

    if boundary_type not in (None, "", "All"):
        query += " AND boundary_type = ?"
        params.append(boundary_type)

    if active_only:
        query += " AND is_active = 1"

    query += """
        ORDER BY
            is_standard DESC,
            is_active DESC,
            project,
            domain,
            surface,
            boundary_type,
            boundary_name
    """

    with get_connection(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]


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


def find_best_boundary(
    project: str,
    domain: str,
    surface: str,
    boundary_type: str = "Stable-Unstable",
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> dict[str, Any] | None:
    """
    Old compatibility function.

    This allows wildcard matching.
    New v1.0 Compare logic should prefer find_active_boundary_exact().
    """
    boundaries = list_boundaries(
        db_path=db_path,
        project=project,
        domain=domain,
        surface=surface,
        boundary_type=boundary_type,
        active_only=True,
    )

    if not boundaries:
        return None

    def score(row: dict[str, Any]) -> int:
        value = 0

        if row.get("project", "") == project:
            value += 4

        if row.get("domain", "") == domain:
            value += 2

        if row.get("surface", "") == surface:
            value += 1

        return value

    return max(boundaries, key=score)


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


def get_boundary_by_id(
    boundary_id: int,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> dict[str, Any] | None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM local_boundaries WHERE id = ?;",
            (boundary_id,),
        ).fetchone()

        return dict(row) if row else None


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


def delete_boundary(
    boundary_id: int,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            "DELETE FROM local_boundaries WHERE id = ?;",
            (boundary_id,),
        )
        connection.commit()
