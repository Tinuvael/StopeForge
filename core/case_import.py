from pathlib import Path

from openpyxl import load_workbook

from db.case_repository import CASE_FIELDS


HEADER_ALIASES = {
    "project": [
        "project",
        "mine",
        "месторождение",
        "проект",
    ],
    "domain": [
        "domain",
        "ore zone",
        "ore_zone",
        "рудная зона",
        "рз",
        "домен",
    ],
    "stope_id": [
        "stope id",
        "stope_id",
        "stope",
        "camera",
        "камера",
        "номер камеры",
        "id камеры",
    ],
    "surface": [
        "surface",
        "face",
        "plane",
        "поверхность",
        "обнажение",
    ],
    "depth_m": [
        "depth",
        "depth m",
        "depth, m",
        "глубина",
        "глубина м",
        "глубина, м",
    ],
    "height_m": [
        "height",
        "height m",
        "height, m",
        "высота",
        "высота м",
        "высота, м",
        "высота этажа",
    ],
    "avg_dip_deg": [
        "avg dip",
        "average dip",
        "average dip, °",
        "average dip deg",
        "средний угол",
        "средний угол падения",
        "угол падения средний",
    ],
    "width_m": [
        "width",
        "width m",
        "width, m",
        "thickness",
        "ore thickness",
        "мощность",
        "ширина",
        "мощность, м",
    ],
    "span_m": [
        "span",
        "span m",
        "span, m",
        "strike length",
        "strike length, m",
        "пролет",
        "пролёт",
        "длина",
        "длина пролета",
        "длина пролёта",
        "пролет по простиранию",
        "пролёт по простиранию",
    ],
    "q_prime": [
        "q'",
        "q prime",
        "qprime",
        "q_prime",
        "q",
        "рейтинг бартона",
        "показатель рейтинга бартона",
    ],
    "a": [
        "a",
        "factor a",
        "stress factor",
        "stress factor a",
        "фактор a",
        "фактор напряжений",
    ],
    "b": [
        "b",
        "factor b",
        "joint factor",
        "joint orientation factor",
        "фактор b",
        "фактор ориентации трещин",
    ],
    "c": [
        "c",
        "factor c",
        "surface factor",
        "gravity factor",
        "фактор c",
        "гравитационный фактор",
    ],
    "n": [
        "n",
        "stability number",
        "mathews stability number",
        "показатель устойчивости",
        "показатель n",
    ],
    "shape_factor_hr_m": [
        "hr",
        "hydraulic radius",
        "hydraulic radius, m",
        "shape factor",
        "shape factor, m",
        "гидравлический радиус",
        "гидравлический радиус hr",
        "коэффициент формы",
    ],
    "stable_hr_limit_m": [
        "stable hr",
        "stable hr limit",
        "hr stable",
        "устойчивый hr",
    ],
    "predicted_state": [
        "predicted",
        "predicted state",
        "calculated state",
        "расчет",
        "расчёт",
        "расчетная оценка",
        "расчётная оценка",
    ],
    "observed_state": [
        "observed",
        "observed state",
        "actual state",
        "fact state",
        "факт",
        "фактическое состояние",
        "устойчивость",
        "категория устойчивости",
    ],
    "comment": [
        "comment",
        "comments",
        "note",
        "notes",
        "комментарий",
        "примечание",
    ],
}


SURFACE_ALIASES = {
    "crown": "Crown",
    "back": "Crown",
    "roof": "Crown",
    "кровля": "Crown",
    "висячий бок": "Hanging wall",
    "hanging wall": "Hanging wall",
    "hw": "Hanging wall",
    "лежачий бок": "Footwall",
    "footwall": "Footwall",
    "fw": "Footwall",
    "end wall": "End wall",
    "endwall": "End wall",
    "борт": "End wall",
    "борта": "End wall",
    "торец": "End wall",
    "торцы": "End wall",
}


STATE_ALIASES = {
    "stable": "Stable",
    "устойчиво": "Stable",
    "устойчивая": "Stable",
    "устойчивые": "Stable",
    "устойчивый": "Stable",
    "un": "Unstable",
    "unstable": "Unstable",
    "failure": "Unstable",
    "minor failure": "Unstable",
    "неустойчиво": "Unstable",
    "неустойчивая": "Unstable",
    "неустойчивые": "Unstable",
    "неустойчивый": "Unstable",
    "caved": "Caved",
    "caving": "Caved",
    "major failure": "Caved",
    "обрушено": "Caved",
    "обрушенная": "Caved",
    "обрушенные": "Caved",
    "обрушенный": "Caved",
    "unknown": "Unknown",
    "": "Unknown",
}


def _normalize_text(value) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = text.replace("\n", " ")
    text = text.replace("ё", "е")

    while "  " in text:
        text = text.replace("  ", " ")

    return text


def _normalize_number(value):
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        return value

    text = str(value).strip().replace(",", ".")

    if text == "":
        return ""

    try:
        return float(text)
    except ValueError:
        return str(value).strip()


def _normalize_surface(value) -> str:
    text = _normalize_text(value)

    return SURFACE_ALIASES.get(text, str(value).strip() if value is not None else "")


def _normalize_state(value) -> str:
    text = _normalize_text(value)

    return STATE_ALIASES.get(text, str(value).strip() if value is not None else "Unknown")


def _build_header_map(header_values: list) -> dict:
    normalized_headers = [_normalize_text(value) for value in header_values]

    header_map = {}

    for field, aliases in HEADER_ALIASES.items():
        normalized_aliases = [_normalize_text(alias) for alias in aliases]

        for column_index, header in enumerate(normalized_headers):
            if header in normalized_aliases:
                header_map[field] = column_index
                break

    return header_map


def _find_header_row(ws, max_rows: int = 20) -> tuple[int, dict]:
    for row_number in range(1, min(ws.max_row, max_rows) + 1):
        values = [cell.value for cell in ws[row_number]]
        header_map = _build_header_map(values)

        if "n" in header_map and "shape_factor_hr_m" in header_map:
            return row_number, header_map

    raise ValueError(
        "Could not find header row. Excel file must contain at least columns for N and HR."
    )


def import_case_histories_from_excel(path: str | Path, sheet_name: str | None = None) -> list[dict]:
    path = Path(path)

    wb = load_workbook(path, data_only=True)

    if sheet_name:
        if sheet_name not in wb.sheetnames:
            raise ValueError(f"Sheet '{sheet_name}' was not found in workbook.")

        ws = wb[sheet_name]
    else:
        ws = wb.active

    header_row, header_map = _find_header_row(ws)

    imported_rows = []

    for row_number in range(header_row + 1, ws.max_row + 1):
        row_values = [cell.value for cell in ws[row_number]]

        raw_row = {}

        for field in CASE_FIELDS:
            column_index = header_map.get(field)

            if column_index is None or column_index >= len(row_values):
                raw_row[field] = ""
            else:
                raw_row[field] = row_values[column_index]

        if raw_row.get("n") in ("", None) and raw_row.get("shape_factor_hr_m") in ("", None):
            continue

        case_row = {field: "" for field in CASE_FIELDS}

        text_fields = [
            "project",
            "domain",
            "stope_id",
            "predicted_state",
            "comment",
        ]

        number_fields = [
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
        ]

        for field in text_fields:
            value = raw_row.get(field, "")
            case_row[field] = "" if value is None else str(value).strip()

        for field in number_fields:
            case_row[field] = _normalize_number(raw_row.get(field, ""))

        case_row["surface"] = _normalize_surface(raw_row.get("surface", ""))
        case_row["observed_state"] = _normalize_state(raw_row.get("observed_state", "Unknown"))

        if case_row["predicted_state"]:
            case_row["predicted_state"] = _normalize_state(case_row["predicted_state"])

        if case_row["project"] == "":
            case_row["project"] = path.stem

        if case_row["observed_state"] == "":
            case_row["observed_state"] = "Unknown"

        imported_rows.append(case_row)

    return imported_rows
