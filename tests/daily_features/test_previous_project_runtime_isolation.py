from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def test_no_previous_project_runtime_dependency():
    text = (ROOT / "pipeline/07_build_daily_features/main.py").read_text(encoding="utf-8").lower()
    assert "previous_project" not in text
    assert "garmin api" not in text
    assert ".xlsx" not in text
