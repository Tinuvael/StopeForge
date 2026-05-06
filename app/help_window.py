import tkinter as tk
from tkinter import ttk
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    import sys

    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parents[1] / relative_path


class CollapsibleSection(ttk.Frame):
    def __init__(self, parent, title: str, expanded: bool = False):
        super().__init__(parent)

        self.title = title
        self.expanded = expanded

        self.header_button = ttk.Button(
            self,
            text=self._header_text(),
            command=self.toggle,
        )
        self.header_button.pack(fill="x", anchor="w", pady=(6, 2))

        self.body = ttk.Frame(self)

        if self.expanded:
            self.body.pack(fill="x", padx=(18, 0), pady=(0, 6))

    def _header_text(self):
        marker = "▼" if self.expanded else "▶"
        return f"{marker} {self.title}"

    def toggle(self):
        self.expanded = not self.expanded
        self.header_button.configure(text=self._header_text())

        if self.expanded:
            self.body.pack(fill="x", padx=(18, 0), pady=(0, 6))
        else:
            self.body.pack_forget()


def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def add_heading(parent, text: str):
    ttk.Label(
        parent,
        text=text,
        font=("Segoe UI", 13, "bold"),
    ).pack(anchor="w", fill="x", pady=(10, 6))


def add_paragraph(parent, text: str):
    ttk.Label(
        parent,
        text=text,
        wraplength=760,
        justify="left",
    ).pack(anchor="w", fill="x", pady=(0, 8))


def add_formula(parent, text: str):
    ttk.Label(
        parent,
        text=text,
        font=("Consolas", 10),
        background="#f4f4f4",
        padding=8,
        justify="left",
    ).pack(anchor="w", fill="x", pady=(0, 8))


def add_image(parent, image_store: list, relative_path: str, caption: str):
    image_path = resource_path(relative_path)

    if not image_path.exists():
        add_paragraph(parent, f"[Image not found: {relative_path}]")
        return

    try:
        image = tk.PhotoImage(file=str(image_path))
    except tk.TclError:
        add_paragraph(parent, f"[Image cannot be loaded: {relative_path}]")
        return

    image_store.append(image)

    ttk.Label(
        parent,
        text=caption,
        font=("Segoe UI", 9, "italic"),
        foreground="#555555",
    ).pack(anchor="w", pady=(8, 2))

    image_label = ttk.Label(parent, image=image)
    image_label.image = image
    image_label.pack(anchor="w", pady=(0, 8))


def render_help_ru(parent, image_store: list):
    add_heading(parent, "StopeForge — справка пользователя")

    quick = CollapsibleSection(parent, "Быстрый рабочий процесс", expanded=True)
    quick.pack(fill="x")

    add_paragraph(
        quick.body,
        "StopeForge предназначен для предварительной инженерной оценки устойчивости "
        "очистных камер по методике Mathews/Potvin, хранения расчетных и фактических "
        "кейсов, построения локальных кривых устойчивости и сравнения стандартной оценки "
        "с локальной калибровкой по накопленному опыту."
    )

    add_paragraph(
        quick.body,
        "Типовой порядок работы: создать Project / месторождение, создать Domain, "
        "заполнить свойства домена, выполнить расчет во вкладке Calculation, сохранить "
        "результат в Calculation Log, при необходимости добавить расчет в Case Histories, "
        "а затем использовать Stability Graph для анализа фактических кейсов и локальных кривых."
    )

    tabs = CollapsibleSection(parent, "Вкладки программы", expanded=False)
    tabs.pack(fill="x")

    add_paragraph(
        tabs.body,
        "Project Tree — общий контекст и фильтр рабочего пространства. "
        "В дереве создаются проекты, домены и стандартные поверхности: Crown, Hanging wall, "
        "Footwall и End wall."
    )

    add_paragraph(
        tabs.body,
        "Calculation — расчет устойчивости камеры по четырем поверхностям. "
        "Для вкладки Calculation выбранная поверхность в дереве игнорируется, потому что расчет "
        "выполняется сразу для всех поверхностей."
    )

    add_paragraph(
        tabs.body,
        "Calculation Log — журнал сохраненных расчетов. Он нужен для хранения пробных вариантов, "
        "сравнения расчетов и подготовки данных для отчетов."
    )

    add_paragraph(
        tabs.body,
        "Case Histories — база расчетных или импортированных кейсов с фактической категорией "
        "устойчивости: Stable, Unstable, Caved или Unknown."
    )

    add_paragraph(
        tabs.body,
        "Stability Graph — график устойчивости HR–N′, на котором отображаются кейсы и локальные "
        "границы устойчивости."
    )

    method = CollapsibleSection(parent, "Методика Mathews/Potvin Stability Graph", expanded=True)
    method.pack(fill="x")

    overview = CollapsibleSection(method.body, "Общая идея метода", expanded=True)
    overview.pack(fill="x")

    add_paragraph(
        overview.body,
        "Методика Mathews/Potvin относится к эмпирическим методам предварительной оценки "
        "устойчивости очистных камер. Основная идея — сопоставить размер и форму расчетной "
        "поверхности камеры с геомеханической способностью массива сохранять устойчивость."
    )

    add_paragraph(
        overview.body,
        "Метод работает не с камерой целиком, а с отдельными поверхностями камеры. "
        "В StopeForge расчет выполняется для Crown, Hanging wall, Footwall и End wall. "
        "Итоговое состояние камеры определяется по наиболее неблагоприятной поверхности."
    )

    add_paragraph(
        overview.body,
        "На графике устойчивости по оси X откладывается гидравлический радиус HR, "
        "а по оси Y — показатель устойчивости N′. Чем больше N′ и меньше HR, тем более "
        "благоприятным считается положение расчетной точки."
    )

    hr = CollapsibleSection(method.body, "Hydraulic Radius, HR", expanded=False)
    hr.pack(fill="x")

    add_paragraph(
        hr.body,
        "Hydraulic Radius, или гидравлический радиус, учитывает геометрию расчетной поверхности. "
        "Он показывает не просто размер поверхности, а соотношение площади и периметра."
    )

    add_formula(
        hr.body,
        "HR = Area / Perimeter\n\n"
        "Для прямоугольной поверхности:\n"
        "Area = a × b\n"
        "Perimeter = 2 × (a + b)\n"
        "HR = (a × b) / (2 × (a + b))"
    )

    add_paragraph(
        hr.body,
        "В StopeForge размеры поверхностей принимаются так:\n\n"
        "Crown: a = stope width / ore thickness, b = stope span / strike length.\n"
        "Hanging wall: a = stope height, b = stope span / strike length.\n"
        "Footwall: a = stope height, b = stope span / strike length.\n"
        "End wall: a = stope height, b = stope width / ore thickness."
    )

    n_section = CollapsibleSection(method.body, "Modified Stability Number, N′", expanded=False)
    n_section.pack(fill="x")

    add_paragraph(
        n_section.body,
        "Показатель устойчивости N′ характеризует способность массива сохранять устойчивость "
        "при заданном качестве массива, напряженном состоянии, ориентации трещин и ориентации "
        "поверхности камеры."
    )

    add_formula(
        n_section.body,
        "N′ = Q′ × A × B × C"
    )

    add_paragraph(
        n_section.body,
        "Где:\n"
        "Q′ — модифицированное качество массива;\n"
        "A — фактор напряженного состояния;\n"
        "B — фактор ориентации трещин;\n"
        "C — фактор ориентации поверхности."
    )

    q_section = CollapsibleSection(method.body, "Q′ — modified Q", expanded=False)
    q_section.pack(fill="x")

    add_paragraph(
        q_section.body,
        "Q′ является модифицированной формой рейтинга Barton Q. В классической записи "
        "используются RQD, Jn, Jr и Ja, а параметры воды и напряжений принимаются равными единице."
    )

    add_formula(
        q_section.body,
        "Q′ = (RQD / Jn) × (Jr / Ja)"
    )

    add_paragraph(
        q_section.body,
        "В StopeForge пользователь задает Q′ напрямую. Можно задать Default Q′ для всех "
        "поверхностей или отдельные значения для Crown, Hanging wall, Footwall и End wall. "
        "Если поверхностное значение не задано, используется Default Q′."
    )

    factor_a = CollapsibleSection(method.body, "Factor A — stress factor", expanded=False)
    factor_a.pack(fill="x")

    add_paragraph(
        factor_a.body,
        "Фактор A учитывает влияние напряженного состояния на устойчивость. "
        "В исходной методике он связан с отношением прочности массива к индуцированным "
        "напряжениям у расчетной поверхности. В StopeForge пока используется упрощенная "
        "автоматическая оценка по вертикальному напряжению."
    )

    add_formula(
        factor_a.body,
        "vertical_stress_mpa = unit_weight_t_m3 × 0.01 × depth_m\n"
        "ratio = UCS / vertical_stress_mpa\n\n"
        "if ratio < 2.25:\n"
        "    A = 0.1\n"
        "elif ratio < 10:\n"
        "    A = 0.1161 × ratio - 0.1613\n"
        "else:\n"
        "    A = 1.0"
    )

    add_paragraph(
        factor_a.body,
        "Также в расчетной форме есть поле A override. Если оно заполнено, StopeForge использует "
        "ручное значение A для выбранной поверхности. Это полезно, если фактор A определен по "
        "отдельному расчету напряжений или численному моделированию."
    )

    add_image(
        factor_a.body,
        image_store,
        "assets/help/factor_a.png",
        "Рисунок — фактор A / Rock Stress Factor"
    )

    factor_b = CollapsibleSection(method.body, "Factor B — joint orientation factor", expanded=False)
    factor_b.pack(fill="x")

    add_paragraph(
        factor_b.body,
        "Фактор B учитывает ориентацию систем трещин относительно расчетной поверхности камеры. "
        "В StopeForge B считается по истинному межплоскостному углу между поверхностью камеры "
        "и каждой системой трещин. Для расчета выбирается минимальное, то есть наиболее "
        "неблагоприятное, значение B."
    )

    add_formula(
        factor_b.body,
        "Для каждой системы трещин:\n\n"
        "true_angle = true interplane angle(surface plane, joint plane)\n"
        "B = function(true_angle)\n\n"
        "Итоговое значение:\n"
        "B = min(B for all joint sets)"
    )

    add_paragraph(
        factor_b.body,
        "Истинный межплоскостной угол считается через полюса плоскостей, а не через простую "
        "разницу азимутов или углов падения. Это важно, потому что две плоскости имеют "
        "пространственную ориентацию, и простая разница углов может дать неверную оценку."
    )

    add_formula(
        factor_b.body,
        "trend = dip_direction + 180°\n"
        "plunge = 90° - dip\n\n"
        "north = cos(trend) × cos(plunge)\n"
        "east  = sin(trend) × cos(plunge)\n"
        "down  = sin(plunge)\n\n"
        "true_angle = acos(|north₁×north₂ + east₁×east₂ + down₁×down₂|)"
    )

    add_formula(
        factor_b.body,
        "Approximation used in StopeForge:\n\n"
        "if angle <= 10°:\n"
        "    B = 0.3 - 0.01 × angle\n"
        "elif angle <= 30°:\n"
        "    B = 0.2\n"
        "elif angle <= 60°:\n"
        "    B = -0.4 + 0.02 × angle\n"
        "else:\n"
        "    B = 0.4 + angle / 150"
    )

    add_image(
        factor_b.body,
        image_store,
        "assets/help/factor_b.png",
        "Рисунок — фактор B / Joint Orientation Factor"
    )

    factor_c = CollapsibleSection(method.body, "Factor C — surface orientation factor", expanded=False)
    factor_c.pack(fill="x")

    add_paragraph(
        factor_c.body,
        "Фактор C учитывает ориентацию расчетной поверхности. В классических источниках могут "
        "встречаться разные варианты записи фактора C. В StopeForge для текущей версии явно "
        "зафиксирована формула ниже."
    )

    add_formula(
        factor_c.body,
        "C = 8 - 6 × cos(dip)\n\n"
        "где dip — угол падения расчетной поверхности от горизонтали."
    )

    add_paragraph(
        factor_c.body,
        "Примеры:\n"
        "Crown с dip = 0°: C = 8 - 6 × cos(0°) = 2.\n"
        "Вертикальная поверхность с dip = 90°: C = 8 - 6 × cos(90°) = 8."
    )

    add_image(
        factor_c.body,
        image_store,
        "assets/help/factor_c.png",
        "Рисунок — фактор C / Surface Orientation Factor"
    )

    limits = CollapsibleSection(method.body, "Stable / Caved HR limits", expanded=False)
    limits.pack(fill="x")

    add_paragraph(
        limits.body,
        "После расчета N′ StopeForge определяет предельные значения HR для устойчивого состояния "
        "и для зоны обрушения. В текущей реализации эти границы заданы как кусочно-линейные "
        "зависимости HR от N′."
    )

    add_paragraph(
        limits.body,
        "Практический смысл такой: расчетная точка поверхности сравнивается с предельными "
        "значениями. Если расчетная длина меньше устойчивого предела — поверхность считается "
        "устойчивой. Если она находится между устойчивым пределом и пределом обрушения — "
        "поверхность считается неустойчивой. Если превышает предел обрушения — поверхность "
        "относится к Caved."
    )

    add_formula(
        limits.body,
        "stable_hr_limit = piecewise_function(N′)\n"
        "caving_hr_limit = piecewise_function(N′)\n\n"
        "equivalent_stable_span = 2 × stable_hr_limit\n"
        "equivalent_caving_span = 2 × caving_hr_limit"
    )

    classification = CollapsibleSection(method.body, "Классификация поверхности", expanded=False)
    classification.pack(fill="x")

    add_formula(
        classification.body,
        "if rating_length >= cave_length:\n"
        "    state = CAVED\n"
        "elif stable_length < rating_length < cave_length:\n"
        "    state = UNSTABLE\n"
        "else:\n"
        "    state = STABLE"
    )

    add_paragraph(
        classification.body,
        "Для Crown, Hanging wall и Footwall в качестве rating length используется длина камеры "
        "по простиранию. Для End wall используется расчетная эффективная длина торца."
    )

    local = CollapsibleSection(parent, "Локальные кривые и адаптация под месторождение", expanded=True)
    local.pack(fill="x")

    add_paragraph(
        local.body,
        "Оригинальная методика Mathews/Potvin является эмпирической и основана на базе "
        "фактических кейсов. Поэтому для конкретного месторождения полезно выполнять локальную "
        "калибровку по собственной базе фактической отработки."
    )

    add_paragraph(
        local.body,
        "В StopeForge локальная адаптация реализуется через Case Histories и Stability Graph. "
        "Пользователь может импортировать или накопить кейсы, задать фактическое состояние "
        "Stable, Unstable или Caved, а затем построить локальные границы устойчивости."
    )

    add_paragraph(
        local.body,
        "Поддерживаются два типа локальных границ:\n"
        "Stable-Unstable — граница между устойчивыми и неустойчивыми кейсами.\n"
        "Unstable-Caved — граница между неустойчивыми и обрушенными кейсами."
    )

    add_formula(
        local.body,
        "Linear curve:\n"
        "N = a × HR + b\n\n"
        "Power curve:\n"
        "N = k × HR^a"
    )

    add_paragraph(
        local.body,
        "В режиме Compare стандартная оценка Mathews/Potvin дополняется сравнением с активными "
        "локальными кривыми для выбранного Project / Domain / Surface. Если активная локальная "
        "кривая не найдена, локальная оценка отображается как Unknown / Not found."
    )

    limitations = CollapsibleSection(parent, "Ограничения и инженерные допущения", expanded=False)
    limitations.pack(fill="x")

    add_paragraph(
        limitations.body,
        "StopeForge не является заменой полноценного геомеханического анализа. Методика "
        "Mathews/Potvin является эмпирическим инструментом предварительной оценки и должна "
        "применяться с учетом применимости исходной базы данных, качества исходных параметров "
        "и локального опыта месторождения."
    )

    add_paragraph(
        limitations.body,
        "Перед использованием результатов необходимо проверить: Q′, геометрию камеры, "
        "ориентацию поверхностей, системы трещин, принятый фактор A, корректность локальных "
        "кривых, а также технологические ограничения отработки."
    )


    disclaimer = CollapsibleSection(parent, "Дисклеймер", expanded=False)
    disclaimer.pack(fill="x")

    add_paragraph(
        disclaimer.body,
        "Программа предназначена как инженерный инструмент поддержки принятия решений. "
        "Результаты должны проверяться квалифицированным геотехническим или геомеханическим "
        "специалистом. Программу не следует использовать как единственное основание для "
        "принятия окончательных проектных решений."
    )



def render_help_en(parent, image_store: list):
    add_heading(parent, "StopeForge — User Guide")

    quick = CollapsibleSection(parent, "Quick workflow", expanded=True)
    quick.pack(fill="x")

    add_paragraph(
        quick.body,
        "StopeForge is intended for preliminary engineering assessment of open-stope "
        "stability using the Mathews/Potvin stability graph approach. It also supports "
        "case history storage, local stability boundary calibration, and comparison "
        "between standard assessment and site-specific local experience."
    )

    add_paragraph(
        quick.body,
        "Typical workflow: create a Project, create a Domain, define domain properties, "
        "run the Calculation, save the result to Calculation Log, add calculated or "
        "imported cases to Case Histories, and use Stability Graph to review case data "
        "and calibrate local boundaries."
    )

    tabs = CollapsibleSection(parent, "Program tabs", expanded=False)
    tabs.pack(fill="x")

    add_paragraph(
        tabs.body,
        "Project Tree — common workspace context and filter. Projects, domains and "
        "standard surfaces are managed here: Crown, Hanging wall, Footwall and End wall."
    )

    add_paragraph(
        tabs.body,
        "Calculation — calculates stope stability for four surfaces. Surface selection "
        "in the Project Tree is ignored on this tab because all four surfaces are calculated "
        "at the same time."
    )

    add_paragraph(
        tabs.body,
        "Calculation Log — stores saved trial calculations. It can be used as a working "
        "calculation library for comparing alternatives and preparing report inputs."
    )

    add_paragraph(
        tabs.body,
        "Case Histories — stores calculated or imported cases with observed stability "
        "state: Stable, Unstable, Caved or Unknown."
    )

    add_paragraph(
        tabs.body,
        "Stability Graph — displays cases on the HR–N′ stability chart and allows local "
        "stability boundaries to be reviewed or calibrated."
    )

    method = CollapsibleSection(parent, "Mathews/Potvin Stability Graph Method", expanded=True)
    method.pack(fill="x")

    overview = CollapsibleSection(method.body, "Method overview", expanded=True)
    overview.pack(fill="x")

    add_paragraph(
        overview.body,
        "The Mathews/Potvin stability graph method is an empirical approach for preliminary "
        "open-stope stability assessment. The main idea is to relate the size and shape "
        "of an excavation surface to the ability of the rock mass to remain stable under "
        "given geological and stress conditions."
    )

    add_paragraph(
        overview.body,
        "The method is applied to individual stope surfaces rather than to the whole stope "
        "as one object. In StopeForge, the assessment is performed for Crown, Hanging wall, "
        "Footwall and End wall. The final stope condition is governed by the most critical "
        "surface."
    )

    add_paragraph(
        overview.body,
        "On the stability graph, the X-axis represents Hydraulic Radius, HR, and the Y-axis "
        "represents the modified Stability Number, N′. In general, higher N′ and lower HR "
        "represent a more favourable stability condition."
    )

    hr = CollapsibleSection(method.body, "Hydraulic Radius, HR", expanded=False)
    hr.pack(fill="x")

    add_paragraph(
        hr.body,
        "Hydraulic Radius accounts for the geometry of the assessed surface. It reflects "
        "not only the size of the exposed surface but also the relationship between its "
        "area and perimeter."
    )

    add_formula(
        hr.body,
        "HR = Area / Perimeter\n\n"
        "For a rectangular surface:\n"
        "Area = a × b\n"
        "Perimeter = 2 × (a + b)\n"
        "HR = (a × b) / (2 × (a + b))"
    )

    add_paragraph(
        hr.body,
        "In StopeForge, surface dimensions are interpreted as follows:\n\n"
        "Crown: a = stope width / ore thickness, b = stope span / strike length.\n"
        "Hanging wall: a = stope height, b = stope span / strike length.\n"
        "Footwall: a = stope height, b = stope span / strike length.\n"
        "End wall: a = stope height, b = stope width / ore thickness."
    )

    n_section = CollapsibleSection(method.body, "Modified Stability Number, N′", expanded=False)
    n_section.pack(fill="x")

    add_paragraph(
        n_section.body,
        "The modified Stability Number, N′, represents the ability of the rock mass to "
        "stand up around the excavation surface under the assumed rock mass quality, "
        "stress conditions, joint orientation and surface orientation."
    )

    add_formula(
        n_section.body,
        "N′ = Q′ × A × B × C"
    )

    add_paragraph(
        n_section.body,
        "Where:\n"
        "Q′ — modified rock mass quality;\n"
        "A — rock stress factor;\n"
        "B — joint orientation factor;\n"
        "C — surface orientation factor."
    )

    q_section = CollapsibleSection(method.body, "Q′ — modified Q", expanded=False)
    q_section.pack(fill="x")

    add_paragraph(
        q_section.body,
        "Q′ is a modified form of the Barton Q rock mass classification. In the Mathews "
        "approach, water and stress reduction parameters are taken as equal to one, so "
        "Q′ is commonly expressed using RQD, Jn, Jr and Ja."
    )

    add_formula(
        q_section.body,
        "Q′ = (RQD / Jn) × (Jr / Ja)"
    )

    add_paragraph(
        q_section.body,
        "In StopeForge, Q′ is entered directly by the user. A Default Q′ value can be "
        "defined for all surfaces, or separate Q′ values can be entered for Crown, "
        "Hanging wall, Footwall and End wall. If a surface-specific value is not provided, "
        "Default Q′ is used."
    )

    factor_a = CollapsibleSection(method.body, "Factor A — rock stress factor", expanded=False)
    factor_a.pack(fill="x")

    add_paragraph(
        factor_a.body,
        "Factor A accounts for the influence of stress conditions on stability. In the "
        "original method it is related to the ratio between intact rock strength and "
        "induced compressive stress at the centre of the stope surface. In the current "
        "StopeForge implementation, a simplified automatic estimate based on vertical "
        "stress is used."
    )

    add_formula(
        factor_a.body,
        "vertical_stress_mpa = unit_weight_t_m3 × 0.01 × depth_m\n"
        "ratio = UCS / vertical_stress_mpa\n\n"
        "if ratio < 2.25:\n"
        "    A = 0.1\n"
        "elif ratio < 10:\n"
        "    A = 0.1161 × ratio - 0.1613\n"
        "else:\n"
        "    A = 1.0"
    )

    add_paragraph(
        factor_a.body,
        "The Calculation form also includes an A override field. If this field is filled, "
        "StopeForge uses the manually entered A value for that surface. This is useful "
        "when A has been estimated from a separate stress analysis, numerical model or "
        "site-specific engineering judgement."
    )

    add_image(
        factor_a.body,
        image_store,
        "assets/help/factor_a.png",
        "Figure — Factor A / Rock Stress Factor"
    )

    factor_b = CollapsibleSection(method.body, "Factor B — joint orientation factor", expanded=False)
    factor_b.pack(fill="x")

    add_paragraph(
        factor_b.body,
        "Factor B accounts for the orientation of joint sets relative to the assessed "
        "stope surface. In StopeForge, B is calculated from the true interplane angle "
        "between the stope surface and each joint set. The lowest B value is used as "
        "the critical value."
    )

    add_formula(
        factor_b.body,
        "For each joint set:\n\n"
        "true_angle = true interplane angle(surface plane, joint plane)\n"
        "B = function(true_angle)\n\n"
        "Final value:\n"
        "B = min(B for all joint sets)"
    )

    add_paragraph(
        factor_b.body,
        "The true interplane angle is calculated using plane poles rather than a simple "
        "difference between dip directions or dip angles. This is important because two "
        "planes are spatial objects, and a simple angular difference may give a misleading "
        "orientation relationship."
    )

    add_formula(
        factor_b.body,
        "trend = dip_direction + 180°\n"
        "plunge = 90° - dip\n\n"
        "north = cos(trend) × cos(plunge)\n"
        "east  = sin(trend) × cos(plunge)\n"
        "down  = sin(plunge)\n\n"
        "true_angle = acos(|north₁×north₂ + east₁×east₂ + down₁×down₂|)"
    )

    add_formula(
        factor_b.body,
        "Approximation used in StopeForge:\n\n"
        "if angle <= 10°:\n"
        "    B = 0.3 - 0.01 × angle\n"
        "elif angle <= 30°:\n"
        "    B = 0.2\n"
        "elif angle <= 60°:\n"
        "    B = -0.4 + 0.02 × angle\n"
        "else:\n"
        "    B = 0.4 + angle / 150"
    )

    add_image(
        factor_b.body,
        image_store,
        "assets/help/factor_b.png",
        "Figure — Factor B / Joint Orientation Factor"
    )

    factor_c = CollapsibleSection(method.body, "Factor C — surface orientation factor", expanded=False)
    factor_c.pack(fill="x")

    add_paragraph(
        factor_c.body,
        "Factor C accounts for the orientation of the assessed surface. Different references "
        "may use different forms of this factor. In the current StopeForge implementation, "
        "the formula below is explicitly fixed."
    )

    add_formula(
        factor_c.body,
        "C = 8 - 6 × cos(dip)\n\n"
        "where dip is the surface dip measured from horizontal."
    )

    add_paragraph(
        factor_c.body,
        "Examples:\n"
        "Crown with dip = 0°: C = 8 - 6 × cos(0°) = 2.\n"
        "Vertical surface with dip = 90°: C = 8 - 6 × cos(90°) = 8."
    )

    add_image(
        factor_c.body,
        image_store,
        "assets/help/factor_c.png",
        "Figure — Factor C / Surface Orientation Factor"
    )

    limits = CollapsibleSection(method.body, "Stable / Caved HR limits", expanded=False)
    limits.pack(fill="x")

    add_paragraph(
        limits.body,
        "After N′ is calculated, StopeForge estimates limiting HR values for stable and "
        "caved conditions. In the current implementation, these limits are defined as "
        "piecewise linear functions of N′."
    )

    add_paragraph(
        limits.body,
        "The practical meaning is as follows: the calculated surface geometry is compared "
        "with the limiting values. If the rating length is below the stable limit, the "
        "surface is classified as Stable. If it lies between the stable and caved limits, "
        "the surface is classified as Unstable. If it exceeds the caved limit, the surface "
        "is classified as Caved."
    )

    add_formula(
        limits.body,
        "stable_hr_limit = piecewise_function(N′)\n"
        "caving_hr_limit = piecewise_function(N′)\n\n"
        "equivalent_stable_span = 2 × stable_hr_limit\n"
        "equivalent_caving_span = 2 × caving_hr_limit"
    )

    classification = CollapsibleSection(method.body, "Surface classification", expanded=False)
    classification.pack(fill="x")

    add_formula(
        classification.body,
        "if rating_length >= cave_length:\n"
        "    state = CAVED\n"
        "elif stable_length < rating_length < cave_length:\n"
        "    state = UNSTABLE\n"
        "else:\n"
        "    state = STABLE"
    )

    add_paragraph(
        classification.body,
        "For Crown, Hanging wall and Footwall, StopeForge uses stope strike length as "
        "the rating length. For End wall, an effective end-wall length is calculated."
    )

    local = CollapsibleSection(parent, "Local curves and site-specific calibration", expanded=True)
    local.pack(fill="x")

    add_paragraph(
        local.body,
        "The Mathews/Potvin method is empirical and depends on case history data. For a "
        "specific deposit, it is often useful to calibrate local stability boundaries "
        "using site-specific mining experience."
    )

    add_paragraph(
        local.body,
        "In StopeForge, local calibration is handled through Case Histories and Stability "
        "Graph. The user can import or accumulate cases, assign observed stability states "
        "and then define local stability boundaries."
    )

    add_paragraph(
        local.body,
        "Two local boundary types are supported:\n"
        "Stable-Unstable — boundary between stable and unstable cases.\n"
        "Unstable-Caved — boundary between unstable and caved cases."
    )

    add_formula(
        local.body,
        "Linear curve:\n"
        "N = a × HR + b\n\n"
        "Power curve:\n"
        "N = k × HR^a"
    )

    add_paragraph(
        local.body,
        "In Compare mode, the standard Mathews/Potvin assessment is supplemented by "
        "comparison with active local curves for the selected Project / Domain / Surface. "
        "If no active local curve is found, the local assessment is displayed as "
        "Unknown / Not found."
    )

    limitations = CollapsibleSection(parent, "Limitations and engineering assumptions", expanded=False)
    limitations.pack(fill="x")

    add_paragraph(
        limitations.body,
        "StopeForge is not a replacement for full geomechanical analysis. The Mathews/Potvin "
        "approach is an empirical preliminary design tool and should be used with awareness "
        "of the applicability of the underlying database, quality of input data and site-specific "
        "mining experience."
    )

    add_paragraph(
        limitations.body,
        "Before using the results, check Q′, stope geometry, surface orientation, joint sets, "
        "stress factor A, local boundaries and operational mining constraints."
    )


    disclaimer = CollapsibleSection(parent, "Disclaimer", expanded=False)
    disclaimer.pack(fill="x")

    add_paragraph(
        disclaimer.body,
        "This software is intended as an engineering decision-support tool. Results must be "
        "checked by a qualified geotechnical or geomechanical specialist. The software should "
        "not be used as the sole basis for final design decisions."
    )




def show_help_window(parent):
    window = tk.Toplevel(parent)
    window.title("StopeForge Help")
    window.geometry("900x720")
    window.minsize(760, 560)

    window.help_images = []

    top_bar = ttk.Frame(window)
    top_bar.pack(fill="x", padx=10, pady=(10, 0))

    ttk.Label(
        top_bar,
        text="Help language:",
        foreground="#555555",
    ).pack(side="left")

    content_area = ttk.Frame(window)
    content_area.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(content_area, highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_area, orient="vertical", command=canvas.yview)

    scroll_frame = ttk.Frame(canvas)
    scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def on_frame_configure(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        canvas.itemconfigure(scroll_window, width=event.width)

    scroll_frame.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def render(language: str):
        clear_frame(scroll_frame)
        window.help_images.clear()

        if language == "RU":
            window.title("Справка StopeForge")
            render_help_ru(scroll_frame, window.help_images)
        else:
            window.title("StopeForge Help")
            render_help_en(scroll_frame, window.help_images)

        canvas.yview_moveto(0)

    ttk.Button(
        top_bar,
        text="English",
        command=lambda: render("EN"),
    ).pack(side="left", padx=(8, 0))

    ttk.Button(
        top_bar,
        text="Русский",
        command=lambda: render("RU"),
    ).pack(side="left", padx=(6, 0))

    render("EN")

    window.transient(parent)
    window.focus_set()
