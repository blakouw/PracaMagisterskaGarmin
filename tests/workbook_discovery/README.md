# tests/01_find_input_workbook

This is the second implemented test-layer module. It validates the production module `pipeline/01_find_input_workbook/`, whose only responsibility is local Garmin workbook discovery for the next pipeline stage.

This test module validates only the local input workbook discovery stage. It does not open, parse, transform or analyse workbook contents.

The documented source rule is to discover files matching garmin_export_*.xlsx and select the first sorted matching file. Any intentional change to this rule must be explicit in the current production contract and test documentation.

The current production contract and `config/project_settings.json` define the active input search configuration as:

- filename pattern: `garmin_export_*.xlsx`
- search directories: `.` and `data/input`
- recursive search: `false`
- selection strategy: `first_path_sorted_ascending`
- multiple matches: deterministic first sorted match, not ambiguity failure

The tests cover a single valid workbook, no workbook, multiple workbook selection, ignored nonmatching files, temporary-looking files, deterministic selection, output artifacts, controlled error reporting, content-reading boundaries, no network or LLM behavior, no Garmin API/auth/token pipeline behavior, and isolation from any previous project runtime.

Synthetic temporary files are used exclusively. These tests must never require a real Garmin export, a real user snapshot, credentials, tokens or network access.

The responsibility boundary is strict: module 01 finds the candidate workbook path, while module 02 is responsible for reading workbook contents.

The current modular project must not restore authentication/profile or Garmin token pipeline responsibilities that existed in earlier source documentation.

Run only this module:

```bat
python -m pytest tests\01_find_input_workbook -q
```

Run the project-contract tests and this module together:

```bat
python -m pytest tests\00_project_contract tests\01_find_input_workbook -q
```
