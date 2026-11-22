from pathlib import Path

from trim_helpers import run_success_fixture


ROOT = Path(__file__).resolve().parents[2]


def test_module_scope_and_isolation(case_root, module03) -> None:
    run_success_fixture(case_root)
    assert module03.execute(case_root) == 0
    source = (ROOT / "pipeline" / "03_trim_workbook" / "main.py").read_text(encoding="utf-8")
    forbidden = ["zipfile", "openpyxl", "read_excel", "garminconnect", "RepoMagi", "call_llm", "calculate_pws", "normalize_daily_records", "convert_units"]
    for term in forbidden:
        assert term not in source
    assert ".xlsx" not in source