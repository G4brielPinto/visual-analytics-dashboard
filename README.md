# Visual Analytics Dashboard

An academic Dash application for exploring UK crime data alongside socio-economic features. The
interface supports category and year selection, scatter plots, parallel coordinates, maps, trend
lines, bar charts, rose diagrams and a Dorling-style map view.

## Included and excluded material

This repository includes the dashboard source code only. The input CSV files and the internal
academic proposal are not versioned because they may be licensed coursework material or contain
data that has not been cleared for redistribution.

No datasets, local paths, credentials or personal contact details are included.

## Features

- crime-count and socio-economic feature comparison;
- interactive filtering by data category and year;
- geographic and layered map views;
- trend and distribution visualisations;
- K-Means-assisted grouping used by the dashboard.

## Setup

Use Python 3.10 or newer in an isolated virtual environment.

~~~bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
~~~

The application starts a local Dash server. Open the local URL displayed in the terminal.

## Local data contract

By default, the app looks for data in the repository's data directory. Alternatively, set the
VAD_DATA_DIR environment variable to a folder that contains this structure:

~~~text
data/
├── CrimeXEmployment/
│   └── *.csv
├── CrimeXPopulation/
│   └── *.csv
└── CrimeXWages/
    └── *.csv
~~~

Each CSV filename must include a four-digit year. The current code expects these core columns:

- Lat and Long for map coordinates;
- Crime Count for the main outcome;
- optional numeric socio-economic feature columns;
- optional city columns, which are retained as categorical information.

All local CSV files are ignored by Git. Do not commit data without explicit permission to share it.

## Reproducibility notes

- The datasets are intentionally absent, so the dashboard cannot display analysis until valid local
  CSV files are supplied.
- The app uses the local data path from VAD_DATA_DIR when set; otherwise it uses data/.
- This is an academic exploratory tool, not a production crime-analysis service.

## Privacy and sharing

The repository is initially private while it is reviewed for a future portfolio release. It excludes
datasets, reports, local machine paths, secrets and personal information.
