# StopeForge

**StopeForge** is an engineering tool for open stope stability assessment using the Mathews–Potvin Stability Graph method with support for site-specific local calibration.

The program is intended for preliminary geomechanical assessment of open stopes and comparison between the standard empirical method and locally calibrated stability boundaries based on actual case histories.

---

## Main capabilities

StopeForge can:

- calculate open stope stability using the Mathews–Potvin method;
- assess four stope surfaces separately:
  - Crown / Back;
  - Hanging wall;
  - Footwall;
  - End wall;
- calculate the stability number `N`;
- calculate hydraulic radius `HR`;
- compare standard and local calibrated assessments;
- store case histories in a local SQLite database;
- store local stability boundaries;
- display case histories on an `HR–N` stability graph;
- export calculation results to Excel;
- export stability graphs to PNG.

---

## Method basis

The stability number is calculated as:

```text
N = Q' × A × B × C
```

Where:

- `Q'` is the modified Barton rock mass quality index;
- `A` is the stress factor;
- `B` is the joint orientation factor;
- `C` is the surface orientation / gravity factor.

In this implementation, factor `B` is calculated using the true interplane angle between the stope surface and the joint set.

Factor `C` is calculated as:

```text
C = 8 - 6 × cos(dip)
```

The assessment is performed for each stope surface separately.

---

## Assessment modes

The calculation tab has two assessment modes:

### Standard

Uses the standard Mathews–Potvin workflow.

This mode is used for a basic preliminary assessment.

### Compare

Calculates the standard assessment and also compares the result with a saved local boundary.

The local boundary is selected by:

```text
Project
Domain
Surface
```

If no matching local boundary is found, the local result is shown as:

```text
Unknown / Not found
```

---

## Case histories

The `Case Histories` tab stores actual mining cases.

A case history can include:

- project;
- domain;
- stope ID;
- surface;
- stope geometry;
- `Q'`, `A`, `B`, `C`, `N`;
- hydraulic radius;
- standard assessment;
- local assessment;
- observed state;
- comment.

Observed state can be edited manually after saving the calculation.

---

## Stability graph

The `Stability Graph` tab displays case history points on an `HR–N` graph.

Available actions:

- filter points by project, domain, surface and observed state;
- show local boundaries;
- manually create local boundaries;
- fit preliminary local boundaries from visible points;
- save, load and delete local boundaries;
- export the graph to PNG.

Local boundaries are currently stored as linear functions:

```text
N = a × HR + b
```

---

## Installation

Create a virtual environment:

```powershell
py -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## Run

Run the program from the project folder:

```powershell
.\.venv\Scripts\python.exe run.py
```

---

## Local data storage

StopeForge stores project data locally in an SQLite database:

```text
data/projects/stopeforge_project.sqlite
```

This database contains:

- case histories;
- saved local boundaries.

The database is created automatically when the program is used.

---

## Basic workflow

### 1. Run a calculation

Open the `Calculation` tab and enter:

- project and domain;
- rock mass parameters;
- stope geometry;
- surface parameters;
- joint sets.

Select assessment mode:

```text
Standard
```

or:

```text
Compare
```

Then click:

```text
Calculate
```

---

### 2. Save the calculation to case histories

After calculation, click:

```text
Add to Case Histories
```

Then go to the `Case Histories` tab and set the observed state manually:

```text
Stable
Unstable
Caved
Unknown
```

---

### 3. Create or save a local boundary

Open the `Stability Graph` tab.

Filter the case histories by:

- project;
- domain;
- surface.

Create or fit a local boundary, then click:

```text
Save boundary
```

The saved boundary can later be used in `Compare` mode.

---

### 4. Compare standard and local assessment

Return to the `Calculation` tab.

Select:

```text
Compare
```

Run the calculation again.

The result table will show:

- standard assessment;
- local assessment;
- local boundary name;
- boundary value `N`.

---

## Important limitations

StopeForge is a preliminary engineering tool based on empirical stability graph methods.

It should not be used as the only basis for final stope design.

The method may be unreliable when:

- the local case history database is too small;
- structural controls dominate stability;
- large discrete wedges are present;
- blasting damage controls failure;
- fill contact is poor or inconsistent;
- stress conditions are outside the empirical experience range;
- the selected local boundary is not representative.

Engineering judgment is required.

---

## Status

StopeForge is currently a working prototype.

The program is intended for engineering review, testing and further development.
