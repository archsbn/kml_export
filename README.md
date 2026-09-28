# kml_export

Generates a KML route file (for Google Earth) from vehicle GPS telemetry exported to Excel.

The route is organized as a folder tree, so it can be viewed by hour, by 10-minute block or by single minute:

```
rota.kml
└─ 2026-09-24 15:00          (folder: 1 hour)
   ├─ 15:20 – 15:29          (folder: 10 minutes)
   │  ├─ Rota 15:26          (line: 1 minute)
   │  ├─ Rota 15:27
   │  └─ ...
   ├─ 15:30 – 15:39
   └─ ...
└─ 2026-09-24 16:00
   └─ ...
```

In Google Earth, checking or unchecking a folder shows or hides everything inside it.

## Requirements

- Python 3.12
- `pandas`, `numpy`, `simplekml`, `openpyxl`

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy simplekml openpyxl
```

## Usage

1. Put the Excel file at `files_in/in.xlsm`.
2. Run:

   ```bash
   python run.py
   ```

3. Open `files_out/rota.kml` in Google Earth.

Input and output paths are set in `run.py` (`CAMINHO_EXCEL` and `CAMINHO_KML`).

## Input file layout

The script reads **only** the sheet named `EXPORT_KML`. Other sheets in the workbook are ignored, and the script fails if this sheet is missing.

| Rule | Details |
| --- | --- |
| Header | Must be on **row 1** (no title or blank rows above it) |
| Required columns | `EVENT_TS`, `LAT_FILE`, `LON_FILE` (case-insensitive) |
| Other columns | Allowed; they are ignored. Column order does not matter |
| `EVENT_TS` | Date/time cell, or text such as `2026-09-24 23:59:59` |
| `LAT_FILE` / `LON_FILE` | Numeric cells in decimal degrees (e.g. `45.14526`) |

Rows with an invalid date or coordinate are dropped silently.

> **Formulas:** if `EXPORT_KML` is filled with formulas (e.g. `=Consulta!F7`), pandas reads the values Excel last saved, not recalculated ones. Save the file in Excel after updating the data.

## How the route is built (`export_rota.py`)

1. Read the `EXPORT_KML` sheet and normalize column names (trim, uppercase, remove `:`).
2. Convert types and drop invalid rows.
3. Sort points by `EVENT_TS`.
4. Group points by hour, then by 10-minute block, then by minute.
5. Create one blue `LineString` (width 3, clamped to ground) per minute.

**Continuity between minutes:** each minute's line starts at the last point of the previous minute, so the route has no gaps. This link is skipped when the gap between the two points exceeds `INTERVALO_MAX_LIGACAO` (default: 2 minutes), so a vehicle stop does not draw a false straight line on the map.

## Project structure

```
.
├── run.py                   # Entry point: calls export_rota.gerar_rota_kml()
├── export_rota.py           # Current script: hour > 10 min > minute route tree
├── export_rota_minut.py     # Older version: hour > minute (legacy column names)
├── export_detail.py         # Older version: one KML per hour with a point per second (legacy)
├── exemplo_kml_estrutura.py # simplekml example
├── files_in/                # Input Excel files
├── files_out/               # Generated KML
└── kml_saida/               # Output of export_detail.py
```

The legacy scripts expect the old column names (`DATA_CREATE_ELEMENT`, `LATITUDE`, `LONGITUDE`) and read `in.xlsx`; they do not work with the current input file.

## KML overview

KML (Keyhole Markup Language) is an XML format used by Google Earth, Google Maps and other GIS tools to describe positions, routes, areas, markers and image overlays.

### Main elements

| Element | Description | Use in this project |
| --- | --- | --- |
| `Placemark` | Container for a geometry with name, description and style | Each minute route |
| `LineString` | Series of connected points | Vehicle route for one minute |
| `Polygon` | Closed area | Not used (e.g. job site boundary) |
| `Folder` | Groups elements; can be nested | Hour and 10-minute groups |
| `Document` | Root container of the file | One per KML file |
| `Style` | Line/icon color, width, size | One shared blue line style |
| `TimeStamp` | Exact moment | Not used (could show position per second) |
| `TimeSpan` | Time interval | Not used (could enable the time slider per minute) |
| `GroundOverlay` | Georeferenced image | Not used (e.g. site map or aerial image) |

### Altitude modes

- `clampToGround`: fixed to the terrain (used here)
- `relativeToGround`: altitude relative to the ground
- `absolute`: real altitude in meters

### Time control

When elements have a `TimeStamp` or `TimeSpan`, Google Earth shows a time slider that allows replaying the route second by second. This is not implemented yet.
