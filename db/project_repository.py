from pathlib import Path
from typing import Any

from db.connection import DEFAULT_PROJECT_DB_PATH, get_connection
from db.schema import initialize_database


DOMAIN_FIELDS = [
    "project_id",
    "domain_name",
    "mining_depth_m",
    "unit_weight_t_m3",
    "ucs_mpa",
    "horizontal_stress_ratio",
    "orebody_dip_direction_deg",
    "orebody_dip_angle_deg",
    "orebody_thickness_m",
    "q_prime_default",
    "q_prime_crown",
    "q_prime_hanging_wall",
    "q_prime_footwall",
    "q_prime_end_wall",
    "joint1_dip_deg",
    "joint1_dip_direction_deg",
    "joint2_dip_deg",
    "joint2_dip_direction_deg",
    "joint3_dip_deg",
    "joint3_dip_direction_deg",
    "joint4_dip_deg",
    "joint4_dip_direction_deg",
    "joint5_dip_deg",
    "joint5_dip_direction_deg",
    "comment",
]


def _none_if_empty(value):
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    return value


def _normalize_domain_row(row: dict[str, Any]) -> dict[str, Any]:
    clean = {}

    for field in DOMAIN_FIELDS:
        value = row.get(field)

        if field in ("project_id", "domain_name", "comment"):
            clean[field] = "" if value is None else value
        else:
            clean[field] = _none_if_empty(value)

    return clean


def list_projects(db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> list[dict[str, Any]]:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM projects
            ORDER BY project_name;
            """
        ).fetchall()

        return [dict(row) for row in rows]


def create_project(
    project_name: str,
    comment: str = "",
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> int:
    initialize_database(db_path)

    project_name = project_name.strip()

    if not project_name:
        raise ValueError("Project name cannot be empty.")

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO projects (project_name, comment)
            VALUES (?, ?)
            ON CONFLICT(project_name)
            DO UPDATE SET
                comment = excluded.comment,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (project_name, comment.strip()),
        )

        connection.commit()

        if cursor.lastrowid:
            return int(cursor.lastrowid)

        row = connection.execute(
            """
            SELECT id
            FROM projects
            WHERE project_name = ?;
            """,
            (project_name,),
        ).fetchone()

        return int(row["id"])


def delete_project(
    project_id: int,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            """
            DELETE FROM projects
            WHERE id = ?;
            """,
            (project_id,),
        )
        connection.commit()


def list_domains(
    project_id: int | None = None,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> list[dict[str, Any]]:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        if project_id is None:
            rows = connection.execute(
                """
                SELECT
                    domains.*,
                    projects.project_name
                FROM domains
                JOIN projects ON projects.id = domains.project_id
                ORDER BY projects.project_name, domains.domain_name;
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT
                    domains.*,
                    projects.project_name
                FROM domains
                JOIN projects ON projects.id = domains.project_id
                WHERE domains.project_id = ?
                ORDER BY domains.domain_name;
                """,
                (project_id,),
            ).fetchall()

        return [dict(row) for row in rows]


def get_domain(
    domain_id: int,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> dict[str, Any] | None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                domains.*,
                projects.project_name
            FROM domains
            JOIN projects ON projects.id = domains.project_id
            WHERE domains.id = ?;
            """,
            (domain_id,),
        ).fetchone()

        return dict(row) if row else None


def upsert_domain(
    row: dict[str, Any],
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> int:
    initialize_database(db_path)

    clean = _normalize_domain_row(row)

    project_id = clean.get("project_id")
    domain_name = str(clean.get("domain_name", "")).strip()

    if not project_id:
        raise ValueError("Project is required for domain.")
    if not domain_name:
        raise ValueError("Domain name cannot be empty.")

    clean["domain_name"] = domain_name

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO domains (
                project_id,
                domain_name,
                mining_depth_m,
                unit_weight_t_m3,
                ucs_mpa,
                horizontal_stress_ratio,
                orebody_dip_direction_deg,
                orebody_dip_angle_deg,
                orebody_thickness_m,
                q_prime_default,
                q_prime_crown,
                q_prime_hanging_wall,
                q_prime_footwall,
                q_prime_end_wall,
                joint1_dip_deg,
                joint1_dip_direction_deg,
                joint2_dip_deg,
                joint2_dip_direction_deg,
                joint3_dip_deg,
                joint3_dip_direction_deg,
                joint4_dip_deg,
                joint4_dip_direction_deg,
                joint5_dip_deg,
                joint5_dip_direction_deg,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, domain_name)
            DO UPDATE SET
                mining_depth_m = excluded.mining_depth_m,
                unit_weight_t_m3 = excluded.unit_weight_t_m3,
                ucs_mpa = excluded.ucs_mpa,
                horizontal_stress_ratio = excluded.horizontal_stress_ratio,
                orebody_dip_direction_deg = excluded.orebody_dip_direction_deg,
                orebody_dip_angle_deg = excluded.orebody_dip_angle_deg,
                orebody_thickness_m = excluded.orebody_thickness_m,
                q_prime_default = excluded.q_prime_default,
                q_prime_crown = excluded.q_prime_crown,
                q_prime_hanging_wall = excluded.q_prime_hanging_wall,
                q_prime_footwall = excluded.q_prime_footwall,
                q_prime_end_wall = excluded.q_prime_end_wall,
                joint1_dip_deg = excluded.joint1_dip_deg,
                joint1_dip_direction_deg = excluded.joint1_dip_direction_deg,
                joint2_dip_deg = excluded.joint2_dip_deg,
                joint2_dip_direction_deg = excluded.joint2_dip_direction_deg,
                joint3_dip_deg = excluded.joint3_dip_deg,
                joint3_dip_direction_deg = excluded.joint3_dip_direction_deg,
                joint4_dip_deg = excluded.joint4_dip_deg,
                joint4_dip_direction_deg = excluded.joint4_dip_direction_deg,
                joint5_dip_deg = excluded.joint5_dip_deg,
                joint5_dip_direction_deg = excluded.joint5_dip_direction_deg,
                comment = excluded.comment,
                updated_at = CURRENT_TIMESTAMP;
            """,
            [clean[field] for field in DOMAIN_FIELDS],
        )

        connection.commit()

        if cursor.lastrowid:
            return int(cursor.lastrowid)

        found = connection.execute(
            """
            SELECT id
            FROM domains
            WHERE project_id = ?
              AND domain_name = ?;
            """,
            (project_id, domain_name),
        ).fetchone()

        return int(found["id"])


def delete_domain(
    domain_id: int,
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            """
            DELETE FROM domains
            WHERE id = ?;
            """,
            (domain_id,),
        )
        connection.commit()

def sync_projects_and_domains_from_case_histories(
    db_path: str | Path = DEFAULT_PROJECT_DB_PATH,
) -> dict[str, int]:
    initialize_database(db_path)

    created_projects = 0
    created_domains = 0
    skipped_rows = 0

    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT
                project,
                domain
            FROM case_histories
            WHERE TRIM(COALESCE(project, '')) <> ''
              AND TRIM(COALESCE(domain, '')) <> ''
            ORDER BY project, domain;
            """
        ).fetchall()

    for row in rows:
        project_name = str(row["project"]).strip()
        domain_name = str(row["domain"]).strip()

        if not project_name or not domain_name:
            skipped_rows += 1
            continue

        existing_project_id = None

        with get_connection(db_path) as connection:
            existing_project = connection.execute(
                """
                SELECT id
                FROM projects
                WHERE project_name = ?;
                """,
                (project_name,),
            ).fetchone()

            if existing_project:
                existing_project_id = int(existing_project["id"])

        if existing_project_id is None:
            project_id = create_project(
                project_name=project_name,
                comment="Created from case histories.",
                db_path=db_path,
            )
            created_projects += 1
        else:
            project_id = existing_project_id

        with get_connection(db_path) as connection:
            existing_domain = connection.execute(
                """
                SELECT id
                FROM domains
                WHERE project_id = ?
                  AND domain_name = ?;
                """,
                (project_id, domain_name),
            ).fetchone()

        if existing_domain:
            continue

        upsert_domain(
            {
                "project_id": project_id,
                "domain_name": domain_name,
                "comment": "Created from case histories.",
            },
            db_path=db_path,
        )
        created_domains += 1

    return {
        "created_projects": created_projects,
        "created_domains": created_domains,
        "skipped_rows": skipped_rows,
    }
