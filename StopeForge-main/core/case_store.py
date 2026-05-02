import csv
from pathlib import Path


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
    "observed_state",
    "comment",
]


DEFAULT_CASES_PATH = Path("data/cases/case_histories.csv")


def ensure_cases_file(path: str | Path = DEFAULT_CASES_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=CASE_FIELDS)
            writer.writeheader()

    return path


def create_empty_cases_file(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CASE_FIELDS)
        writer.writeheader()

    return path


def load_cases(path: str | Path = DEFAULT_CASES_PATH) -> list[dict]:
    path = ensure_cases_file(path)

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = []

        for row in reader:
            normalized_row = {field: row.get(field, "") for field in CASE_FIELDS}
            rows.append(normalized_row)

        return rows


def save_cases(rows: list[dict], path: str | Path = DEFAULT_CASES_PATH) -> None:
    path = ensure_cases_file(path)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CASE_FIELDS)
        writer.writeheader()

        for row in rows:
            clean_row = {field: row.get(field, "") for field in CASE_FIELDS}
            writer.writerow(clean_row)


def append_cases(new_rows: list[dict], path: str | Path = DEFAULT_CASES_PATH) -> None:
    path = ensure_cases_file(path)

    existing_rows = load_cases(path)
    existing_rows.extend(new_rows)
    save_cases(existing_rows, path)
