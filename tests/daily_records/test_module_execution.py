import subprocess
import sys
from daily_helpers import ROOT, read_json

def test_module_execution_on_current_safe_artifacts() -> None:
    if sys.platform.startswith("win"):
        result = subprocess.run(["cmd", "/c", "pipeline\\05_normalize_daily_records\\run.bat"], cwd=ROOT, text=True, capture_output=True, check=False)
    else:
        result = subprocess.run([sys.executable, "pipeline/05_normalize_daily_records/main.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    base = ROOT / "data" / "pipeline" / "05_normalize_daily_records"
    assert read_json(base / "run_manifest.json")["domain_status"] == "normalized"
