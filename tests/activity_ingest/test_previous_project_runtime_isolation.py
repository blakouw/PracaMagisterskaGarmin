from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_previous_project_runtime_isolation() -> None:
    files = [
        ROOT / "config" / "garmin_activity_ingest_v1.json",
        ROOT / "pipeline" / "04_garmin_activity_ingest" / "main.py",
        ROOT / "pipeline" / "04_garmin_activity_ingest" / "garmin_client_adapter.py",
        ROOT / "pipeline" / "04_garmin_activity_ingest" / "run.bat",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "RepoMagi" not in combined
    assert "from app." not in combined
    assert "import app." not in combined
    assert "previous_project_runtime_dependency_allowed\": false" in (ROOT / "config" / "garmin_activity_ingest_v1.json").read_text(encoding="utf-8")
