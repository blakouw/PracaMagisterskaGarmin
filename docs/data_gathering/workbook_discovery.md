# 01 Find Input Workbook

Status: implemented.

This module locates local Garmin workbook candidates and deterministically selects the formal input workbook for the next pipeline step. It is the first data-facing module after `00_project_contract`.

This module only locates and selects the input workbook. Workbook parsing belongs exclusively to module 02_read_xlsx_workbook.

## Inputs

- `config/project_settings.json`
- Local filesystem paths explicitly listed in `input_workbook.search_directories`

The default search configuration is:

- pattern: `garmin_export_*.xlsx`
- directories: `.`, `data/input`
- recursive: `false`
- selection strategy: `first_path_sorted_ascending`

## Outputs

Artifacts are written to `data/pipeline/01_find_input_workbook/`:

- `workbook_manifest.json`
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

## Selection Rules

The module searches only configured directories within the new project root. It converts matches to root-relative paths, removes duplicates, sorts paths ascending as text, and selects the first sorted candidate.

If no workbook is found, execution still succeeds and the domain status is `missing`. The manifest sets `selected_workbook` to `null` and `ready_for_next_module` to `false`.

If multiple workbooks are found, execution succeeds, all candidates are listed, and the first sorted path is selected. The manifest and log include a warning that the deterministic selection strategy was applied.

The workbook may contain private health and activity data. This module reports only file metadata and never reads XLSX contents, sheets, cells or columns.

The new project does not use the previous project at runtime. Module 01 does not search old project folders, import old code, copy workbook files, read tokens or use Garmin API data.

## Run

```bat
pipeline\01_find_input_workbook\run.bat
```

## Tests

```bat
.venv\Scripts\python.exe -m pytest tests\01_find_input_workbook
```

## Visualization

```bat
visualization\01_find_input_workbook\run_visualization.bat
```
