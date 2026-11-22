# 03 Trim Workbook

Status: implemented.

This module performs explicit KEEP/DROP selection and writes trimmed sheet artifacts only. Data normalization, date joining, unit conversions and metric calculations belong exclusively to later modules.

Module 03 consumes raw sheet artifacts produced by `02_read_xlsx_workbook` and the public policy `config/garmin_trim_policy_v1.json`. It never reopens the original `.xlsx` workbook.

## Inputs

- `data/pipeline/02_read_xlsx_workbook/workbook_structure.json`
- `data/pipeline/02_read_xlsx_workbook/raw_sheets_manifest.json`
- `data/pipeline/02_read_xlsx_workbook/raw_sheets/*.json`
- `config/garmin_trim_policy_v1.json`

## KEEP/DROP Model

Sheets are classified as `KEEP_REQUIRED`, `KEEP_OPTIONAL`, `DROP_NOT_USED`, `MISSING_REQUIRED` or `MISSING_OPTIONAL`. Columns are classified as `KEEP_REQUIRED`, `KEEP_OPTIONAL`, `DROP_NOT_USED`, `MISSING_REQUIRED` or `MISSING_OPTIONAL`.

Required sheet:

- `Daily_Summary`

Optional kept sheets when present:

- `Daily_Sleep`
- `Daily_HRV`
- `Daily_RHR`
- `Daily_Stress`
- `Daily_Respiration`
- `Daily_SpO2`
- `Daily_Intensity_Minutes`
- `Range_Daily_Steps`
- `Activities`
- `Range_Body_Composition`

`Daily_Summary` must contain `calendarDate` and `activeKilocalories`. Missing optional sheets or optional columns are reported as warnings and do not block the module if required foundations are present.

## Outputs

Artifacts are written to `data/pipeline/03_trim_workbook/`:

- `trimmed_sheets/*.csv`
- `trimmed_sheets_manifest.json`
- `trim_summary.json`
- `trim_report.md`
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

CSV files use UTF-8, keep columns in policy order, preserve record order from raw sheet artifacts and preserve source values without conversions. Missing values are written as empty CSV fields.

## Privacy And Scope

Trimmed CSV files may contain private Garmin health and sport data and must remain local. This module does not normalize data, join sheets by `calendarDate`, convert units, calculate metrics, call Garmin API, call LLM, implement an API or implement UI. The project does not depend on the previous project at runtime.

The current policy uses exact sheet and column names only. It should be reviewed after the first run on a real Garmin export because development fixtures may not expose every real Garmin header.

## Run

```bat
pipeline\03_trim_workbook\run.bat
```

## Tests

```bat
python -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook
```

## Visualization

```bat
visualization\03_trim_workbook\run_visualization.bat
```