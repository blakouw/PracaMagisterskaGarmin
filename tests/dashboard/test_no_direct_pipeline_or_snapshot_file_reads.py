from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "pipeline/18_angular_dashboard_ui/app/src"


def test_no_direct_pipeline_or_snapshot_file_reads():
    text = "\n".join(path.read_text(encoding="utf-8") for path in SRC.rglob("*") if path.is_file())
    assert "data/pipeline" not in text
    assert "data/published" not in text
    assert "/api/v1/" in (SRC / "api/dashboardApi.ts").read_text(encoding="utf-8")
