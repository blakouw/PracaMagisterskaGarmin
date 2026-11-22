from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import artifact_json, execute, make_case_root, write_settings


def test_missing_config_is_controlled_error(tmp_path: Path) -> None:
    root = tmp_path / "synthetic_project"
    root.mkdir()

    assert execute(root) == 1

    run_manifest = artifact_json(root, "run_manifest.json")
    errors = artifact_json(root, "errors.json")
    assert run_manifest["execution_status"] == "failed"
    assert run_manifest["domain_status"] == "not_evaluated"
    assert errors["errors"][0]["code"] == "CONFIG_READ_ERROR"


def test_configured_missing_directory_reports_missing_without_traceback(tmp_path: Path) -> None:
    root = tmp_path / "synthetic_project"
    root.mkdir()
    write_settings(root, search_directories=["missing_input"])

    assert execute(root) == 0

    run_manifest = artifact_json(root, "run_manifest.json")
    errors = artifact_json(root, "errors.json")
    assert run_manifest["execution_status"] == "success"
    assert run_manifest["domain_status"] == "missing"
    assert errors["errors"] == []


def test_invalid_search_directory_outside_project_is_controlled_error(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    write_settings(root, search_directories=[".."])

    assert execute(root) == 1

    errors = artifact_json(root, "errors.json")
    assert errors["errors"][0]["code"] == "CONFIG_VALIDATION_ERROR"
    assert "outside the project root" in errors["errors"][0]["message"]
