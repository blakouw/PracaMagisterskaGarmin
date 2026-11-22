# 02 Read XLSX Workbook

Status: implemented.

This module reads the workbook formally selected by `01_find_input_workbook` and serializes raw workbook structure and sheet data for `03_trim_workbook`.

This module reads and serializes raw workbook structure and sheet data only. KEEP/DROP selection and column trimming belong exclusively to module 03_trim_workbook.

## Inputs

- `data/pipeline/01_find_input_workbook/workbook_manifest.json`
- The selected local Garmin workbook referenced by that manifest

The module does not search for workbooks on its own and does not run module 01 automatically.

## Outputs

Artifacts are written to `data/pipeline/02_read_xlsx_workbook/`:

- `workbook_structure.json` - structural summary with sheet names, counts and headers.
- `raw_sheets_manifest.json` - formal registry of raw sheet artifacts for module 03.
- `raw_sheets/*.json` - one private raw JSON artifact per workbook sheet.
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

## XLSX Reader

The module uses a small custom ZIP/XML reader based on Python standard library modules: `zipfile` and `xml.etree.ElementTree`. It reads:

- `xl/workbook.xml`
- `xl/_rels/workbook.xml.rels`
- optional `xl/sharedStrings.xml`
- worksheet XML files referenced by workbook relationships

Supported values include numbers, shared strings, inline strings, booleans and empty cells. Formula results are read only when Excel has stored a cached value; formulas are never calculated by this module.

The reader does not implement a complete Excel engine. It does not interpret styles, visual formatting, date serials or formulas.

## Raw Sheet Format

The first non-empty row in each sheet is treated as the header row for structural reporting. Empty headers receive deterministic technical names such as `__column_B`. Duplicate headers receive suffixes such as `value__2`. Empty sheets still produce a raw artifact with warnings and no rows.

Raw sheet artifacts may contain private Garmin health and activity data. They must remain local and are ignored by Git.

## Privacy And Scope

This module does not select required sheets, classify KEEP/DROP sheets, trim columns, normalize records, calculate metrics, call Garmin API, call LLM, implement an API server or implement UI. It does not depend on the previous project at runtime.

## Run

```bat
pipeline\02_read_xlsx_workbook\run.bat
```

## Tests

```bat
python -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook
```

## Visualization

```bat
visualization\02_read_xlsx_workbook\run_visualization.bat
```
