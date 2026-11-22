import json

from trim_helpers import run_success_fixture


def test_trim_report_summary_and_manifests_are_written(case_root, module03) -> None:
    run_success_fixture(case_root)
    assert module03.execute(case_root) == 0
    artifact_dir = case_root / "data" / "pipeline" / "03_trim_workbook"
    for filename in ["trimmed_sheets_manifest.json", "trim_summary.json", "trim_report.md", "run_manifest.json", "run_log.txt", "errors.json"]:
        assert (artifact_dir / filename).is_file(), filename
    summary = json.loads((artifact_dir / "trim_summary.json").read_text(encoding="utf-8"))
    report = (artifact_dir / "trim_report.md").read_text(encoding="utf-8")
    run_manifest = json.loads((artifact_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert summary["total_kept_columns_count"] >= 3
    assert "KEEP - Sheets retained" in report
    assert "DROP - Sheets not used" in report
    assert "MISSING - Expected sheets not found" in report
    assert run_manifest["execution_status"] == "success"
    assert run_manifest["domain_status"] == "trimmed"