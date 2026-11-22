# 00 Project Contract Tests

This test module validates the foundational architecture contract of the repository. It does not calculate, recompute or validate wellness scores.

The test layer follows the same modular isolation principle as the production pipeline: each test module is implemented independently inside tests/<module_id>/ and validates only its declared responsibility.

This module guards the separation between pipeline, tests and visualization, the privacy boundary of local data, the absence of removed authentication and Garmin token stages, and the runtime isolation from any previous project.

These tests use only repository metadata, public configuration and synthetic paths. They must never require real Garmin exports, real user snapshots, tokens, secrets or LLM calls.

## Scope

`pipeline/00_project_contract/` is the production contract module. `tests/00_project_contract/` is the architectural test module. `visualization/00_project_contract/` is the preview/debug layer for module 00 artifacts.

The tests cover:

- repository structure and root folders,
- `config/pipeline_modules.json`,
- production module contracts,
- dependency graph validity and cycle absence,
- absence of removed modules,
- runtime isolation from previous projects,
- `.gitignore` privacy protections,
- public secret scanning with low-noise patterns,
- cross-module responsibility boundaries,
- execution contract of `pipeline/00_project_contract`.

The tests do not run the analytical pipeline on private data, do not parse real Garmin exports, do not call Garmin APIs, do not call LLMs, do not start API/UI/package servers and do not build Windows release packages.

## Run

From the project root:

```bat
python -m pytest tests\00_project_contract -q
```

Or:

```bat
tests\00_project_contract\run_tests.bat
```

Failures in this module usually indicate an architectural contract violation: a missing module contract, an invalid registry dependency, a privacy boundary regression, accidental public exposure, or reintroduction of a removed responsibility. Later test modules are implemented separately and are not required by this module unless the project registry explicitly marks them as implemented.
