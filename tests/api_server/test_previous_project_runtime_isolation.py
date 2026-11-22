from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_previous_project_runtime_isolation():
    text=(ROOT/"pipeline/17_local_api_server/api_app.py").read_text(encoding="utf-8") + (ROOT/"pipeline/17_local_api_server/main.py").read_text(encoding="utf-8")
    assert "previous_project" not in text
    assert "RepoMagi" not in text
