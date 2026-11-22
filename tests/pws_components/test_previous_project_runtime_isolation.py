from pathlib import Path


def test_no_old_runtime_or_api_refs():
    root = Path(__file__).resolve().parents[2]
    text = (root / "pipeline/10_compute_pws_components/main.py").read_text(encoding="utf-8").lower()
    assert "garminconnect" not in text
    assert ".xlsx" not in text
    assert "previous_project" not in text
    assert "openai" not in text
