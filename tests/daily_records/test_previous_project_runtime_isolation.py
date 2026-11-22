from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def test_previous_project_runtime_isolation() -> None:
    combined = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in ["pipeline/05_normalize_daily_records/main.py", "pipeline/05_normalize_daily_records/run.bat", "config/garmin_daily_normalization_v1.json"])
    assert "RepoMagi" not in combined
    assert "from app." not in combined
    assert "import app." not in combined
    assert "garminconnect" not in combined
