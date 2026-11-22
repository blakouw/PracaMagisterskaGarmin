from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_module_source_has_no_normalization_metrics_llm_or_network_tests() -> None:
    source = (ROOT / "pipeline" / "04_garmin_activity_ingest" / "main.py").read_text(encoding="utf-8")
    adapter = (ROOT / "pipeline" / "04_garmin_activity_ingest" / "garmin_client_adapter.py").read_text(encoding="utf-8")
    assert "normalize_activities(" not in source
    assert "merge_workbook" not in source
    assert "calculate_pws" not in source
    assert "call_llm" not in source
    assert "requests." not in source
    assert "openpyxl" not in source
    assert "pandas" not in source
    assert "download_activity" in adapter
