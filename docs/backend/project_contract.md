# 00 Project Contract

Status: implemented.

This module defines the foundation for the local Garmin analytics project. It creates and validates the project structure, the formal module registry, module contracts, public policy files, the local secret boundary and the reporting artifacts used by later modules.

The project is built as an artifact pipeline because every significant processing step must leave a durable output on disk. Each following module consumes a formal artifact from the previous module instead of relying on hidden in-memory state. That makes each step independently runnable, testable and inspectable.

The three main implementation areas are:

- `pipeline/` - production modules, one responsibility per folder.
- `tests/` - tests mapped to pipeline modules.
- `visualization/` - text or visual previews for module artifacts.

Supporting directories are:

- `data/` - local inputs and generated artifacts.
- `config/` - public configuration and algorithmic policies.
- `shared/` - technical helpers shared by multiple modules only when needed.

The new project must not depend on the previous project at runtime. The older project may be read as implementation reference and may be used once as a source for copying local secrets into `data/local_secrets/`, but this pipeline must not import, execute, require, or modify that old project.

## Module Order

1. `00_project_contract`
2. `01_find_input_workbook`
3. `02_read_xlsx_workbook`
4. `03_trim_workbook`
5. `04_garmin_activity_ingest`
6. `05_normalize_daily_records`
7. `06_normalize_activities`
8. `07_build_daily_features`
9. `08_compute_load_metrics`
10. `09_compute_readiness`
11. `10_compute_pws_components`
12. `11_compute_pws_weights`
13. `12_compute_pws_score`
14. `13_validate_llm_weight_influence`
15. `14_build_coach_context`
16. `15_build_dashboard_payload`
17. `16_persist_local_snapshot`
18. `17_local_api_server`
19. `18_angular_dashboard_ui`
20. `19_packaging_windows`

Currently modules 00 through 13 and modules 15 through 19 are implemented. Module 14 remains planned. Future modules must be implemented one at a time and must not be implemented as a side effect of work on earlier modules.

## Artifact Versioning

Each module writes artifacts to `data/pipeline/<module_id>/`. Executable modules must write `run_manifest.json`, `run_log.txt` and `errors.json` in addition to their domain artifacts. Contract versions are explicit in each module `contract.json`; future incompatible changes should bump the version and preserve a clear migration path.

## PWS Rules

PWS means `Poziom Wysportowania`. It is a future 0-100 training decision-support indicator based on four 0-1 components: `LQ`, `REC`, `CAP` and `VS`. Module 00 only stores the policy contract in `config/pws_policy_v1.json`; it does not calculate PWS.

## LLM Role

LLM is disabled by default. In `deterministic` mode the project must work without any LLM and produce deterministic PWS outputs. In `llm_assisted` mode a future LLM may only propose a small bounded weight correction from controlled context. The LLM is not a metric calculator and cannot independently approve final PWS weights; a later deterministic validation module must decide whether any LLM influence is applied.

## Run

Run module 00:

```bat
pipeline\00_project_contract\run.bat
```

Run visualization:

```bat
visualization\00_project_contract\run_visualization.bat
```

Run tests:

```bat
python -m pytest tests\00_project_contract
```

