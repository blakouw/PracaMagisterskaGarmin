import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_module_03_contract_is_implemented() -> None:
    contract = read_json("pipeline/03_trim_workbook/contract.json")
    assert contract["module_id"] == "03_trim_workbook"
    assert contract["status"] == "implemented"
    assert contract["run_command"] == "pipeline/03_trim_workbook/run.bat"
    assert "data/pipeline/02_read_xlsx_workbook/raw_sheets/*.json" in contract["inputs"]
    assert "data/pipeline/03_trim_workbook/trimmed_sheets/*.csv" in contract["outputs"]
    assert "parse_xlsx_zip_xml" in contract["prohibited_responsibilities"]
    assert "normalize_daily_records" in contract["prohibited_responsibilities"]
    assert "call_llm" in contract["prohibited_responsibilities"]


def test_registry_statuses_after_module_03() -> None:
    modules = read_json("config/pipeline_modules.json")["modules"]
    for module in modules[:14]:
        assert module["status"] == "implemented", module["id"]
    for module in modules[14:]:
        expected = "implemented" if module["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"} else "planned"
        assert module["status"] == expected, module["id"]


