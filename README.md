# StopeForge

**StopeForge** is a desktop geotechnical tool for preliminary open-stope stability assessment using the Mathews/Potvin Stability Graph approach.

The program is designed for engineering workflows where open stope surfaces are assessed individually, case histories are stored, and local stability curves are calibrated using site-specific mining experience.

---

## Version

**Current release:** `1.0.0`

---

## Main Features

### Mathews/Potvin Stability Assessment

StopeForge calculates stability parameters for four standard stope surfaces:

- Crown
- Hanging wall
- Footwall
- End wall

For each surface, the program calculates:

- Hydraulic Radius, HR
- Stress factor, A
- Joint orientation factor, B
- Surface orientation factor, C
- Stability Number, N'
- Stable HR limit
- Caved HR limit
- Stable span
- Cave span
- Standard stability state

The stability state is classified as:

- Stable
- Unstable
- Caved

---

## Calculation Logic

The main stability number is calculated as:

```text
N' = Q' × A × B × C
```

Where:

```text
Q' = Modified rock mass quality
A  = Stress factor
B  = Joint orientation factor
C  = Surface orientation factor
```

Hydraulic radius is calculated as:

```text
HR = Area / Perimeter
```

For a rectangular surface:

```text
HR = (a × b) / (2 × (a + b))
```

In the current StopeForge implementation, the surface orientation factor is calculated as:

```text
C = 8 - 6 × cos(dip)
```

Where `dip` is the surface dip measured from horizontal.

---

## Project Tree

StopeForge uses a project tree as the main workspace context.

Project structure:

```text
Project / Deposit
└── Domain
    ├── Crown
    ├── Hanging wall
    ├── Footwall
    └── End wall
```

The project tree is used for:

- selecting the active project;
- selecting the active domain;
- filtering case histories;
- filtering the stability graph;
- applying domain properties to the calculation form.

For the Calculation and Calculation Log tabs, surface selection is ignored because the calculation is performed for all four surfaces.

For the Case Histories and Stability Graph tabs, surface selection is used as a filter.

---

## Domain Properties

Each domain can store default calculation parameters.

### Basic rock mass and stress parameters

- Mining depth
- Unit weight
- UCS
- Horizontal stress ratio K / λ

### Orebody parameters

- Orebody dip direction
- Orebody dip angle
- Orebody thickness

### Q' values

- Default Q'
- Crown Q'
- Hanging wall Q'
- Footwall Q'
- End wall Q'

If only Default Q' is provided, it is applied to all surfaces.

If surface-specific Q' values are provided, they are used for the corresponding surfaces.

### Joint sets

Up to five joint sets can be stored for each domain:

```text
Set 1 dip / dip direction
Set 2 dip / dip direction
Set 3 dip / dip direction
Set 4 dip / dip direction
Set 5 dip / dip direction
```

---

## Calculation Tab

The Calculation tab is used to run the main Mathews/Potvin assessment.

The calculation is performed for all four surfaces at the same time.

The results table is arranged by surface:

```text
Parameter | Hanging wall | Footwall | Crown | End wall
```

Stability states are visually highlighted:

```text
Stable   = green
Unstable = yellow
Caved    = red
```

Calculation modes:

```text
Standard = standard Mathews/Potvin assessment
Compare  = standard assessment plus comparison with active local curves
```

---

## Calculation Log

The Calculation Log tab is used to store trial calculations.

It can be used as a working calculation library for:

- comparing multiple stope options;
- keeping calculation alternatives;
- preparing engineering reports;
- reviewing previous calculation scenarios.

The log can be filtered by Project and Domain using the Project Tree.

---

## Case Histories

The Case Histories tab stores calculated or imported case history data.

Each case includes:

- project;
- domain;
- stope ID;
- surface;
- geometry;
- Q';
- A, B, C;
- N';
- HR;
- predicted state;
- observed state;
- comment.

Observed state can be edited manually:

```text
Unknown
Stable
Unstable
Caved
```

Case histories are stored in an SQLite project database.

---

## Stability Graph

The Stability Graph tab displays case histories on the HR–N' stability chart.

It supports filtering by:

- Project
- Domain
- Surface

The graph is used for reviewing case history data and calibrating local stability curves.

---

## Local Curves

StopeForge supports local site-specific stability curves.

Supported boundary types:

```text
Stable-Unstable
Unstable-Caved
```

Supported curve modes:

```text
Linear:
N = a × HR + b

Power:
N = k × HR^a
```

Saved local curves can be set as active and used in Compare mode.

This allows the standard Mathews/Potvin assessment to be compared with site-specific empirical experience.

---

## Help and About

StopeForge includes built-in Help and About windows.

The Help window contains:

- user workflow;
- program tab descriptions;
- Mathews/Potvin method explanation;
- formulas;
- factor A / B / C descriptions;
- local calibration notes;
- limitations and disclaimer.

The Help window supports English and Russian text.

---

## Current Scope

Included in version `1.0.0`:

- Mathews/Potvin stability calculation;
- calculation of four standard surfaces;
- project/domain tree;
- domain property storage;
- calculation log;
- case history database;
- stability graph;
- local curve creation and activation;
- Compare mode;
- Excel export;
- built-in Help and About windows.

---

## Deferred Scope

The following features are intentionally deferred to future versions:

- full UI redesign;
- dark theme;
- dashboard;
- advanced reporting;
- support design module;
- cablebolt density calculation;
- cablebolt spacing calculation;
- cablebolt length calculation;
- full probabilistic analysis;
- full localization of the entire UI.

Support design and cablebolt calculations are not included in version `1.0.0`.

---

## Installation for Users

For release builds, download the packaged executable from the release page.

On Windows:

```text
StopeForge.exe
```

Run the executable directly.

No Python installation is required for the packaged version.

---

## Running from Source

### Requirements

- Python 3.12+
- Windows recommended for the current packaged workflow

### Create virtual environment

```powershell
py -m venv .venv
```

### Activate virtual environment

```powershell
.\.venv\Scripts\activate
```

### Install dependencies

```powershell
pip install -r requirements.txt
```

### Run the application

```powershell
python run.py
```

---

## Running Tests

```powershell
python -m pytest -q
```

---

## Building Windows Executable

Example PyInstaller command:

```powershell
pyinstaller --onefile --windowed --icon=assets/icons/stopeforge_icon.ico --add-data "assets;assets" run.py
```

The generated executable will be located in:

```text
dist/
```

---

## Project Structure

Typical project structure:

```text
StopeForge/
├── app/
│   ├── main_window.py
│   ├── splash.py
│   ├── info_windows.py
│   ├── help_window.py
│   └── config.py
├── assets/
│   ├── icons/
│   └── help/
├── core/
│   ├── stability.py
│   ├── mathews_factors.py
│   ├── local_assessment.py
│   └── models.py
├── db/
│   ├── connection.py
│   ├── schema.py
│   ├── project_repository.py
│   ├── case_repository.py
│   └── boundary_repository.py
├── gui/
│   ├── calculation_tab.py
│   ├── project_overview_tab.py
│   ├── case_histories_tab.py
│   ├── stability_graph_tab.py
│   └── project_tree_panel.py
├── tests/
├── run.py
├── requirements.txt
└── README.md
```

---

## Engineering Disclaimer

StopeForge is an engineering decision-support tool.

The results must be checked by a qualified geotechnical or geomechanical specialist.

The software should not be used as the sole basis for final design decisions.

Users are responsible for checking:

- input data quality;
- applicability of the Mathews/Potvin method;
- rock mass parameters;
- stress assumptions;
- structural data;
- domain selection;
- local calibration curves;
- mining and operational constraints.

---

## Copyright

Copyright © 2026 Емшанов Евгений. All rights reserved.

---

## License

This software is proprietary unless a separate license file states otherwise.

Use, copying, modification, redistribution, or commercial application of the software is not permitted without written permission from the copyright holder.
