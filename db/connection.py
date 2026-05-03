from pathlib import Path
import sqlite3
import sys


def get_app_root() -> Path:
    """
    Development:
        project root, where run.py is located.

    PyInstaller EXE / APP:
        folder where the executable is located.

    Windows packaged layout:
        dist/StopeForge/StopeForge.exe

    macOS packaged layout:
        dist/StopeForge.app/Contents/MacOS/StopeForge
    """
    if getattr(sys, "frozen", False):
        executable_path = Path(sys.executable).resolve()

        # macOS .app:
        # StopeForge.app/Contents/MacOS/StopeForge
        # We want the folder containing StopeForge.app.
        if sys.platform == "darwin" and ".app" in executable_path.as_posix():
            for parent in executable_path.parents:
                if parent.suffix == ".app":
                    return parent.parent

        # Windows:
        # StopeForge/StopeForge.exe
        return executable_path.parent

    # db/connection.py -> project root
    return Path(__file__).resolve().parents[1]


APP_ROOT = get_app_root()
DEFAULT_PROJECT_DB_PATH = APP_ROOT / "data" / "projects" / "stopeforge_project.sqlite"


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
