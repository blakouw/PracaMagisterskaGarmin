from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def test_no_api_or_ui_code():
    text = (ROOT / "pipeline/16_persist_local_snapshot/main.py").read_text(encoding="utf-8").lower()
    assert "fastapi" not in text
    assert "flask" not in text
    assert "angular" not in text
