from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import all_artifact_text, artifact_dir, artifact_json, create_file, execute, make_case_root


def test_success_output_artifacts_are_written_and_parseable(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    assert execute(root) == 0

    output_dir = artifact_dir(root)
    expected_files = {"workbook_manifest.json", "run_manifest.json", "run_log.txt", "errors.json"}
    assert expected_files <= {path.name for path in output_dir.iterdir() if path.is_file()}

    workbook_manifest = artifact_json(root, "workbook_manifest.json")
    run_manifest = artifact_json(root, "run_manifest.json")
    errors = artifact_json(root, "errors.json")

    assert workbook_manifest["selected_workbook"]["relative_path"] == "data/input/garmin_export_2026-05-01.xlsx"
    assert run_manifest["generated_artifacts"] == [
        "data/pipeline/01_find_input_workbook/workbook_manifest.json",
        "data/pipeline/01_find_input_workbook/run_manifest.json",
        "data/pipeline/01_find_input_workbook/run_log.txt",
        "data/pipeline/01_find_input_workbook/errors.json",
    ]
    assert errors["errors"] == []


def test_artifacts_do_not_contain_workbook_contents_tokens_or_previous_project_paths(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    assert execute(root) == 0

    text = all_artifact_text(root)
    assert "oauth_token" not in text
    assert "access_token" not in text
    assert "refresh_token" not in text
    assert "RepoMagi" not in text
