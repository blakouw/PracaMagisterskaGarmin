import json
import os
import subprocess
import sys

from trim_helpers import run_success_fixture, ROOT


def test_module_03_run_bat_generates_required_artifacts() -> None:
    run_success_fixture(ROOT)
    if os.name == "nt":
        result = subprocess.run(["cmd", "/c", "pipeline\\03_trim_workbook\\run.bat"], cwd=ROOT, text=True, capture_output=True, check=False)
    else:
        result = subprocess.run([sys.executable, "pipeline/03_trim_workbook/main.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    artifact_dir = ROOT / "data" / "pipeline" / "03_trim_workbook"
    for filename in ["trimmed_sheets_manifest.json", "trim_summary.json", "trim_report.md", "run_manifest.json", "run_log.txt", "errors.json"]:
        assert (artifact_dir / filename).is_file(), filename
    errors = json.loads((artifact_dir / "errors.json").read_text(encoding="utf-8"))
    manifest = json.loads((artifact_dir / "trimmed_sheets_manifest.json").read_text(encoding="utf-8"))
    assert errors == {"module_id": "03_trim_workbook", "errors": []}
    assert manifest["ready_for_next_module"] is True