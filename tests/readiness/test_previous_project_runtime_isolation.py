from pathlib import Path


def test_no_old_runtime_or_api_references():
    root = Path(__file__).resolve().parents[2]
    text = (root / "pipeline/09_compute_readiness/main.py").read_text(encoding="utf-8").lower()
    assert "garminconnect" not in text
    assert ".xlsx" not in text
    assert "previous_project" not in text
    assert "openai" not in text
