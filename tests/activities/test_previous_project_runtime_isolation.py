from activity_helpers import ROOT

def test_previous_project_runtime_isolation():
    paths = ["pipeline/06_normalize_activities/main.py", "pipeline/06_normalize_activities/run.bat", "config/garmin_activity_normalization_v1.json"]
    combined = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in paths)
    assert "C:\\Users\\ckami\\Documents\\RepoMagi" not in combined
    assert "from app." not in combined
    assert "import app." not in combined
