# StopeForge

**StopeForge** is an engineering tool for open stope stability assessment and site-specific calibration using the Mathews–Potvin stability graph method.

The project is focused on preliminary underground open stope stability assessment. It calculates the modified Q value, Mathews adjustment factors, stability number, hydraulic radius, and empirical stability zones for individual stope surfaces.

The long-term goal of StopeForge is to combine standard empirical design charts with site-specific case history data, allowing engineers to calibrate stability boundaries for local rock mass and mining conditions.

## Purpose

Open stope stability assessment is often based on empirical methods such as the Mathews–Potvin stability graph. These methods are useful for preliminary design but depend strongly on the quality and relevance of the underlying case history database.

StopeForge aims to help engineers:

- calculate stability parameters in a structured way;
- compare planned stope surfaces against empirical stability boundaries;
- store site-specific stope performance observations;
- visualize local case histories on the stability graph;
- adjust empirical boundaries based on observed mine performance.

## Planned Features

### Core calculations

- Modified Q value, Q'
- Mathews stability number, N
- Rock stress factor, A
- Joint orientation adjustment factor, B
- Surface orientation factor, C
- Hydraulic radius / shape factor calculation
- Stability assessment for individual stope surfaces

### Case history database

- Add observed stope cases
- Store geometry, rock mass quality, adjustment factors, stability number, hydraulic radius, and observed performance
- Classify observed stability as stable, minor failure, major failure, or caved
- Filter case histories by mine, orebody, level, domain, or surface type

### Visualization

- Mathews–Potvin stability graph
- N vs hydraulic radius chart
- Log-scale plotting
- Standard empirical boundaries
- User-added case history points
- Site-specific calibrated boundaries

### Calibration

- Manual site-specific correction factor
- Local boundary adjustment based on observed stable and failed cases
- Future support for statistical calibration and logistic regression

## Project Structure

```text
stopeforge/
├── app/                  # Application configuration and main window
├── core/                 # Engineering calculation logic
├── gui/                  # User interface tabs and widgets
├── data/                 # Local case history data and presets
├── exports/              # Exported reports and charts
├── tests/                # Tests
├── run.py                # Application entry point
├── requirements.txt      # Python dependencies
└── README.md
```
Method Overview


The Mathews–Potvin method is based on the relationship between:

•	Mathews stability number, N 
•	Hydraulic radius, HR 


The stability number is calculated as:
N = Q' × A × B × C
where:

•	Q' is the modified NGI Q value; 
•	A is the rock stress factor; 
•	B is the joint orientation adjustment factor; 
•	C is the surface orientation factor. 


The hydraulic radius is calculated as:
HR = Area / Perimeter
Each stope surface should be assessed separately:

•	hanging wall; 
•	footwall; 
•	crown / back; 
•	end wall. 



Development Roadmap



v0.1 — Basic Calculator


•	Project structure 
•	Basic Mathews–Potvin calculation module 
•	Hydraulic radius calculation 
•	Simple GUI input form 
•	Basic stability classification 



v0.2 — Stability Graph


•	N–HR chart 
•	Log-scale graph 
•	Standard empirical boundaries 
•	Plot calculated design points 



v0.3 — Case History Storage


•	Add local case history database 
•	Save and load observed stope cases 
•	Plot observed cases on the graph 



v0.4 — Site-Specific Calibration


•	Manual site correction factor 
•	Adjusted local stability boundaries 
•	Comparison between standard and calibrated design limits 



v0.5 — Statistical Calibration


•	Regression-based local boundary fitting 
•	Probability-based stability assessment 
•	Support for stable / failure / major failure classes 



Installation


Clone the repository:

```bash
git clone https://github.com/Tinuvael/stopeforge.git
cd stopeforge
```
Create a virtual environment:
python -m venv .venv
Activate the virtual environment:
.venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
Run the application:
python run.py


Status


This project is in early development.

The first goal is to build a clean and reliable Mathews–Potvin calculator with a simple graphical interface. Advanced calibration and statistical tools will be added after the basic calculation workflow is stable.



## License

This project is proprietary software.

Use of this software is allowed only under a separate written license agreement or written permission from the author.

See [LICENSE.txt](./LICENSE.txt) for details.

## Disclaimer

This software is an auxiliary engineering calculation tool. It does not replace professional engineering judgment or independent verification.

See [DISCLAIMER.md](./DISCLAIMER.md) before using any results for engineering decisions.

