from pathlib import Path


def test_no_previous_project_runtime_reference():
    main_text = (Path(__file__).resolve().parents[2] / "pipeline/11_compute_pws_weights/main.py").read_text(encoding="utf-8").lower()
    assert "previousproject" not in main_text
    assert "stary" not in main_text
