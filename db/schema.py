from pathlib import Path

from db.connection import get_connection, DEFAULT_PROJECT_DB_PATH


SCHEMA_VERSION = 1

def _column_exists(connection, table_name: str, column_name: str) -> bool:
    columns = connection.execute(f"PRAGMA table_info({table_name});").fetchall()
    return any(column["name"] == column_name for column in columns)


def _add_column_if_missing(connection, table_name: str, column_name: str, column_sql: str) -> None:
    if not _column_exists(connection, table_name, column_name):
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql};"
        )

def initialize_database(db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> None:
    with get_connection(db_path) as connection:
        connection.executescript(

                        """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS case_histories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project TEXT NOT NULL DEFAULT '',
                domain TEXT NOT NULL DEFAULT '',
                stope_id TEXT NOT NULL DEFAULT '',
                surface TEXT NOT NULL DEFAULT '',

                depth_m REAL,
                height_m REAL,
                avg_dip_deg REAL,
                width_m REAL,
                span_m REAL,

                q_prime REAL,
                a REAL,
                b REAL,
                c REAL,
                n REAL,

                shape_factor_hr_m REAL,
                stable_hr_limit_m REAL,

                predicted_state TEXT NOT NULL DEFAULT '',
                observed_state TEXT NOT NULL DEFAULT 'Unknown',

                comment TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_case_histories_project
                ON case_histories(project);

            CREATE INDEX IF NOT EXISTS idx_case_histories_domain
                ON case_histories(domain);

            CREATE INDEX IF NOT EXISTS idx_case_histories_surface
                ON case_histories(surface);

            CREATE INDEX IF NOT EXISTS idx_case_histories_observed_state
                ON case_histories(observed_state);

            CREATE TABLE IF NOT EXISTS local_boundaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project TEXT NOT NULL DEFAULT '',
                domain TEXT NOT NULL DEFAULT '',
                surface TEXT NOT NULL DEFAULT '',

                boundary_name TEXT NOT NULL DEFAULT '',
                boundary_type TEXT NOT NULL DEFAULT 'Stable-Unstable',

                mode TEXT NOT NULL DEFAULT 'linear',

                slope REAL NOT NULL,
                intercept REAL NOT NULL,

                percentile REAL,
                margin REAL,

                is_standard INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,

                comment TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(project, domain, surface, boundary_name, boundary_type)
            );

            CREATE INDEX IF NOT EXISTS idx_local_boundaries_project
                ON local_boundaries(project);

            CREATE INDEX IF NOT EXISTS idx_local_boundaries_domain
                ON local_boundaries(domain);

            CREATE INDEX IF NOT EXISTS idx_local_boundaries_surface
                ON local_boundaries(surface);

            CREATE INDEX IF NOT EXISTS idx_local_boundaries_type
                ON local_boundaries(boundary_type);
            """
        )
            
        _add_column_if_missing(
            connection,
            "case_histories",
            "calculation_mode",
            "TEXT NOT NULL DEFAULT 'Standard'",
        )
        _add_column_if_missing(
            connection,
            "case_histories",
            "standard_state",
            "TEXT NOT NULL DEFAULT ''",
        )
        _add_column_if_missing(
            connection,
            "case_histories",
            "local_state",
            "TEXT NOT NULL DEFAULT ''",
        )
        _add_column_if_missing(
            connection,
            "case_histories",
            "local_boundary_name",
            "TEXT NOT NULL DEFAULT ''",
        )
        _add_column_if_missing(
            connection,
            "case_histories",
            "local_boundary_n",
            "REAL",
        )
        _add_column_if_missing(
            connection,
            "case_histories",
            "actual_hr_m",
            "REAL",
        )



        connection.execute(
            """
            INSERT OR REPLACE INTO app_metadata(key, value)
            VALUES('schema_version', ?);
            """,
            (str(SCHEMA_VERSION),),
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL UNIQUE,
                comment TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                domain_name TEXT NOT NULL,

                mining_depth_m REAL,
                unit_weight_t_m3 REAL,
                ucs_mpa REAL,
                horizontal_stress_ratio REAL,

                orebody_dip_direction_deg REAL,
                orebody_dip_angle_deg REAL,
                orebody_thickness_m REAL,

                q_prime_default REAL,
                q_prime_crown REAL,
                q_prime_hanging_wall REAL,
                q_prime_footwall REAL,
                q_prime_end_wall REAL,

                joint1_dip_deg REAL,
                joint1_dip_direction_deg REAL,
                joint2_dip_deg REAL,
                joint2_dip_direction_deg REAL,
                joint3_dip_deg REAL,
                joint3_dip_direction_deg REAL,
                joint4_dip_deg REAL,
                joint4_dip_direction_deg REAL,
                joint5_dip_deg REAL,
                joint5_dip_direction_deg REAL,

                comment TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE(project_id, domain_name)
            );
            """
        )



        connection.commit()
