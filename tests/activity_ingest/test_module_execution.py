import subprocess
import sys

from activity_ingest_helpers import ROOT, read_json


def test_run_bat_or_python_execution_default_disabled() -> None:
    if sys.platform.startswith("win"):
        result = subprocess.run(["cmd", "/c", "pipeline\\04_garmin_activity_ingest\\run.bat"], cwd=ROOT, text=True, capture_output=True, check=False)
    else:
        result = subprocess.run([sys.executable, "pipeline/04_garmin_activity_ingest/main.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    base = ROOT / "data" / "pipeline" / "04_garmin_activity_ingest"
    manifest = read_json(base / "activity_ingest_manifest.json")
    assert manifest["status"] == "skipped_disabled"
    assert (base / "run_manifest.json").is_file()
    assert (ROOT / "pipeline" / "04_garmin_activity_ingest" / "run.bat").is_file()
