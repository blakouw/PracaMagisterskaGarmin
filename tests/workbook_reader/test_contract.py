import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_module_02_contract_is_implemented() -> None:
    contract = read_json("pipeline/02_read_xlsx_workbook/contract.json")
    assert contract["module_id"] == "02_read_xlsx_workbook"
    assert contract["status"] == "implemented"
    assert contract["run_command"] == "pipeline/02_read_xlsx_workbook/run.bat"
    assert "data/pipeline/01_find_input_workbook/workbook_manifest.json" in contract["inputs"]
    assert "data/pipeline/02_read_xlsx_workbook/raw_sheets/*.json" in contract["outputs"]
    assert "select_required_sheets" in contract["prohibited_responsibilities"]
    assert "trim_columns" in contract["prohibited_responsibilities"]
    assert "depend_on_previous_project_runtime" in contract["prohibited_responsibilities"]


def test_registry_statuses_after_module_02() -> None:
    modules = read_json("config/pipeline_modules.json")["modules"]
    by_id = {module["id"]: module for module in modules}
    assert by_id["00_project_contract"]["status"] == "implemented"
    assert by_id["01_find_input_workbook"]["status"] == "implemented"
    assert by_id["02_read_xlsx_workbook"]["status"] == "implemented"
    assert by_id["03_trim_workbook"]["status"] == "implemented"
    assert by_id["04_garmin_activity_ingest"]["status"] == "implemented"
    assert by_id["05_normalize_daily_records"]["status"] == "implemented"
    assert by_id["06_normalize_activities"]["status"] == "implemented"
    assert by_id["07_build_daily_features"]["status"] == "implemented"
    assert by_id["08_compute_load_metrics"]["status"] == "implemented"
    assert by_id["09_compute_readiness"]["status"] == "implemented"
    assert by_id["10_compute_pws_components"]["status"] == "implemented"
    assert by_id["11_compute_pws_weights"]["status"] == "implemented"
    assert by_id["12_compute_pws_score"]["status"] == "implemented"
    for module in modules[14:]:
        expected = "implemented" if module["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"} else "planned"
        assert module["status"] == expected, module["id"]


def test_gitignore_protects_module_02_private_artifacts() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "garmin_export_*.xlsx" in gitignore
    assert "data/input/*.xlsx" in gitignore
    assert "data/local_secrets/*" in gitignore
    assert "data/pipeline/02_read_xlsx_workbook/" in gitignore




