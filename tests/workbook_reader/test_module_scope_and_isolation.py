from pathlib import Path

from xlsx_helpers import create_xlsx, write_workbook_manifest


ROOT = Path(__file__).resolve().parents[2]


def test_module_scope_and_isolation(case_root, module02) -> None:
    workbook = case_root / "data" / "input" / "garmin_export_scope.xlsx"
    create_xlsx(workbook, [{"name": "Scope", "rows": [["a"], [1]]}])
    write_workbook_manifest(case_root, "data/input/garmin_export_scope.xlsx")
    before = workbook.read_bytes()

    assert module02.execute(case_root) == 0

    after = workbook.read_bytes()
    source = (ROOT / "pipeline" / "02_read_xlsx_workbook" / "main.py").read_text(encoding="utf-8")
    forbidden_terms = [
        "openpyxl",
        "pandas.read_excel",
        "RepoMagi",
        "garminconnect",
        "select_required_sheets(",
        "classify_keep_drop",
        "normalize_daily_records(",
        "calculate_pws(",
        "call_llm(",
    ]
    for term in forbidden_terms:
        assert term not in source
    assert before == after
