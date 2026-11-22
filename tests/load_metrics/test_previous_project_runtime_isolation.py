from pathlib import Path


def test_no_previous_project_or_api_runtime_references():
    root = Path(__file__).resolve().parents[2]
    text = (root / "pipeline/08_compute_load_metrics/main.py").read_text(encoding="utf-8").lower()
    assert "garminconnect" not in text
    assert ".xlsx" not in text
    assert "previous_project" not in text
    assert "openai" not in text
