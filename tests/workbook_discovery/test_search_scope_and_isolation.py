from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import artifact_json, create_file, execute, make_case_root, manifest, write_settings


def test_unconfigured_directories_are_not_searched(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["data/input"])
    create_file(root, "not_configured/garmin_export_hidden.xlsx")

    assert execute(root) == 0

    payload = manifest(root)
    assert payload["status"] == "missing"
    assert payload["candidates_count"] == 0


def test_search_directories_must_not_escape_project_root(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    write_settings(root, search_directories=[".."])

    assert execute(root) == 1

    run_manifest = artifact_json(root, "run_manifest.json")
    errors = artifact_json(root, "errors.json")
    assert run_manifest["execution_status"] == "failed"
    assert run_manifest["domain_status"] == "not_evaluated"
    assert errors["errors"][0]["code"] == "CONFIG_VALIDATION_ERROR"


def test_module_does_not_require_previous_project_to_report_missing(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["."])

    assert execute(root) == 0
    assert manifest(root)["status"] == "missing"
