import subprocess, sys
from activity_helpers import ROOT, read_json

def test_module_execution_default_empty_or_local():
    if sys.platform.startswith("win"):
        result = subprocess.run(["cmd", "/c", r"pipeline\06_normalize_activities\run.bat"], cwd=ROOT, text=True, capture_output=True, check=False)
    else:
        result = subprocess.run([sys.executable, "pipeline/06_normalize_activities/main.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    payload = read_json(ROOT / "data/pipeline/06_normalize_activities/activities_normalized.json")
    assert payload["ready_for_next_module"] is True
