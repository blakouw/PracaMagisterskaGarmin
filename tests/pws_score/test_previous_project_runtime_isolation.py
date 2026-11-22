from pathlib import Path


def test_previous_project_runtime_isolation():
    text = (Path(__file__).resolve().parents[2] / "pipeline/12_compute_pws_score/main.py").read_text(encoding="utf-8").lower()
    assert "previousproject" not in text
    assert "stary" not in text
