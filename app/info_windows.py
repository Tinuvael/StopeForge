import tkinter as tk
from tkinter import ttk, scrolledtext


APP_VERSION = "1.0 MVP"


HELP_TEXT_EN = """StopeForge — User Guide

Main workflow

1. Project Tree
Create or select a project and domain in the Project Tree.
Each domain can store default rock mass, stress, orebody and joint set parameters.

2. Calculation
Use the Calculation tab to run the Mathews/Potvin stability assessment.
When a domain is selected in the Project Tree, domain properties are automatically applied to the calculation form.

Calculation modes:
- Standard: standard Mathews/Potvin assessment.
- Compare: standard assessment plus saved local curves.

The calculation is performed for four surfaces:
- Crown
- Hanging wall
- Footwall
- End wall

3. Calculation Log
Save trial calculations to the Calculation Log.
This tab is intended as a working calculation library for comparing multiple stope options.

4. Case Histories
Use Case Histories to store calculated or imported cases with observed stability states:
- Stable
- Unstable
- Caved
- Unknown

Observed state can be edited manually after cases are added.

5. Stability Graph
Use the Stability Graph to view case histories and calibrate local curves.

Local curve types:
- Stable-Unstable
- Unstable-Caved

Curve modes:
- Linear: N = a × HR + b
- Power: N = k × HR^a

Manual curve editing:
Enable edit points on graph, move curve points, then save the curve.
Saved curves can be set active and used in Compare mode.

6. Project Tree filtering
The Project Tree controls filtering for:
- Stability Graph
- Case Histories
- Calculation Log

For Calculation and Calculation Log, surface nodes are ignored.
For Case Histories and Stability Graph, surface nodes can be used as filters.

Notes

StopeForge is intended as an engineering decision-support tool.
Always check input data, assumptions and results before using them in design decisions.

Support design / cablebolt design is not included in the current version and is deferred to a future release.
"""


HELP_TEXT_RU = """StopeForge — Справка пользователя

Основной рабочий процесс

1. Дерево проекта

Создайте или выберите проект / месторождение и домен в дереве проекта.
Домен может хранить базовые параметры массива, напряженного состояния, рудного тела и систем трещин.

2. Calculation

Вкладка Calculation используется для расчета устойчивости по методике Mathews/Potvin.
При выборе домена в дереве проекта параметры домена автоматически подставляются в расчетную форму.

Режимы расчета:
- Standard: стандартная оценка Mathews/Potvin.
- Compare: стандартная оценка плюс сравнение с сохраненными локальными кривыми.

Расчет выполняется для четырех поверхностей:
- Crown / кровля
- Hanging wall / висячий бок
- Footwall / лежачий бок
- End wall / торец

3. Calculation Log

Вкладка Calculation Log используется как журнал расчетов.
Сюда можно сохранять пробные варианты расчетов для последующего сравнения и использования в отчетах.

4. Case Histories

Вкладка Case Histories используется для хранения расчетных или импортированных кейсов с фактической категорией устойчивости:

- Stable / устойчивая
- Unstable / неустойчивая
- Caved / обрушенная
- Unknown / неизвестно

Фактическую категорию устойчивости можно редактировать вручную после добавления кейсов.

5. Stability Graph

Вкладка Stability Graph используется для просмотра кейсов на графике устойчивости и калибровки локальных кривых.

Типы локальных кривых:
- Stable-Unstable: граница между устойчивыми и неустойчивыми кейсами.
- Unstable-Caved: граница между неустойчивыми и обрушенными кейсами.

Режимы кривых:
- Linear: N = a × HR + b
- Power: N = k × HR^a

Ручное редактирование кривой:
Включите Edit points on graph, переместите точки кривой на графике и сохраните кривую.
Сохраненную кривую можно сделать активной и использовать в режиме Compare.

6. Фильтрация через дерево проекта

Дерево проекта управляет фильтрацией для вкладок:
- Stability Graph
- Case Histories
- Calculation Log

Для Calculation и Calculation Log поверхности игнорируются.
Для Case Histories и Stability Graph поверхности можно использовать как фильтр.

Примечания

StopeForge является инженерным инструментом поддержки принятия решений.
Исходные данные, допущения и результаты расчета должны проверяться квалифицированным геотехническим или геомеханическим специалистом.

Модуль проектирования крепи / cablebolt design в текущую версию не входит и отложен на будущие версии.
"""


ABOUT_TEXT = """StopeForge is a geotechnical tool for Mathews/Potvin stability assessment, case history storage, local curve calibration, and project/domain-based stope analysis.

StopeForge — геотехнический инструмент для оценки устойчивости очистных камер по методике Mathews/Potvin, хранения базы фактической отработки, калибровки локальных кривых и анализа камер по проектам и доменам.
"""


DISCLAIMER_TEXT = """Disclaimer:
This software is intended as an engineering decision-support tool. Results must be checked by a qualified geotechnical or geomechanical specialist. The software should not be used as the sole basis for final design decisions.

Дисклеймер:
Программа предназначена как инженерный инструмент поддержки принятия решений. Результаты должны проверяться квалифицированным геотехническим или геомеханическим специалистом. Программу не следует использовать как единственное основание для принятия окончательных проектных решений.
"""


def show_help_window(parent):
    window = tk.Toplevel(parent)
    window.title("StopeForge Help")
    window.geometry("760x620")
    window.minsize(650, 500)

    top_bar = ttk.Frame(window)
    top_bar.pack(fill="x", padx=10, pady=(10, 0))

    ttk.Label(
        top_bar,
        text="Help language:",
        foreground="#555555",
    ).pack(side="left")

    text = scrolledtext.ScrolledText(
        window,
        wrap="word",
        font=("Segoe UI", 10),
    )
    text.pack(fill="both", expand=True, padx=10, pady=10)

    def set_help_language(language: str):
        text.configure(state="normal")
        text.delete("1.0", "end")

        if language == "RU":
            window.title("Справка StopeForge")
            text.insert("1.0", HELP_TEXT_RU)
        else:
            window.title("StopeForge Help")
            text.insert("1.0", HELP_TEXT_EN)

        text.configure(state="disabled")

    ttk.Button(
        top_bar,
        text="English",
        command=lambda: set_help_language("EN"),
    ).pack(side="left", padx=(8, 0))

    ttk.Button(
        top_bar,
        text="Русский",
        command=lambda: set_help_language("RU"),
    ).pack(side="left", padx=(6, 0))

    set_help_language("EN")

    window.transient(parent)
    window.focus_set()


def show_about_window(parent):
    window = tk.Toplevel(parent)
    window.title("About StopeForge")
    window.geometry("620x460")
    window.resizable(False, False)

    content = ttk.Frame(window, padding=18)
    content.pack(fill="both", expand=True)

    ttk.Label(
        content,
        text="StopeForge",
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w", pady=(0, 8))

    ttk.Label(
        content,
        text=f"Version: {APP_VERSION}",
        font=("Segoe UI", 10),
    ).pack(anchor="w", pady=(0, 12))

    ttk.Label(
        content,
        text=ABOUT_TEXT,
        wraplength=570,
        justify="left",
    ).pack(anchor="w", pady=(0, 14))

    ttk.Label(
        content,
        text="Copyright © 2026. All rights reserved.",
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w", pady=(0, 14))

    ttk.Label(
        content,
        text=DISCLAIMER_TEXT,
        wraplength=570,
        justify="left",
        foreground="#555555",
    ).pack(anchor="w", pady=(0, 14))

    ttk.Button(
        content,
        text="Close",
        command=window.destroy,
    ).pack(anchor="e", pady=(10, 0))

    window.transient(parent)
    window.focus_set()
