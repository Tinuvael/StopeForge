import csv
from pathlib import Path


BOUNDARY_FIELDS = [
    "project",
    "domain",
    "surface",
    "boundary_name",
    "mode",
    "slope",
    "intercept",
    "percentile",
    "margin",
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
