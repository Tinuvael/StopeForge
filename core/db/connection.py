from pathlib import Path
import sqlite3


DEFAULT_PROJECT_DB_PATH = Path("data/projects/stopeforge_project.sqlite")


def ensure_project_dir(db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_connection(db_path: str | Path = DEFAULT_PROJECT_DB_PATH) -> sqlite3.Connection:
    db_path = ensure_project_dir(db_path)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON;")

    return connection
