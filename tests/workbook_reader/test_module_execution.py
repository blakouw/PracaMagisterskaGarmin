import json
import importlib.util
from pathlib import Path

from xlsx_helpers import create_xlsx, write_workbook_manifest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "pipeline" / "02_read_xlsx_workbook" / "main.py"


def load_module():
    spec = importlib.util.spec_from_file_location("read_xlsx_workbook_module_execution", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_module_02_execute_generates_required_artifacts_in_synthetic_project(tmp_path: Path) -> None:
    case_root = tmp_path / "synthetic_project"
    workbook = case_root / "data" / "input" / "garmin_export_module02_fixture.xlsx"
    create_xlsx(workbook, [{"name": "Run", "rows": [["name", "value"], ["fixture", 1]]}])
    write_workbook_manifest(case_root, "data/input/garmin_export_module02_fixture.xlsx")
    module = load_module()

    exit_code = module.execute(case_root)

    assert exit_code == 0
    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    for filename in ["workbook_structure.json", "raw_sheets_manifest.json", "run_manifest.json", "run_log.txt", "errors.json"]:
        assert (artifact_dir / filename).is_file(), filename

    run_manifest = json.loads((artifact_dir / "run_manifest.json").read_text(encoding="utf-8"))
    errors = json.loads((artifact_dir / "errors.json").read_text(encoding="utf-8"))
    structure = json.loads((artifact_dir / "workbook_structure.json").read_text(encoding="utf-8"))
    log_text = (artifact_dir / "run_log.txt").read_text(encoding="utf-8")

    assert run_manifest["execution_status"] == "success"
    assert run_manifest["domain_status"] == "parsed"
    assert errors == {"module_id": "02_read_xlsx_workbook", "errors": []}
    assert structure["sheets_count"] == 1
    assert "keep_drop_filtering_performed=false" in log_text
    assert "domain_calculations_performed=false" in log_text
