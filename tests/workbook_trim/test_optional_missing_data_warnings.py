import json

from trim_helpers import copy_policy, write_module02_artifacts, daily_summary_sheet


def test_missing_optional_data_warns_but_does_not_block(case_root, module03) -> None:
    copy_policy(case_root)
    write_module02_artifacts(case_root, [daily_summary_sheet()])
    assert module03.execute(case_root) == 0
    summary = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "trim_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "trimmed"
    assert summary["missing_optional_sheets_count"] > 0
    assert summary["optional_columns_missing"]
    assert summary["warnings"]