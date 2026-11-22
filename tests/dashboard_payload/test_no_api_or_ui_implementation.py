from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_no_api_ui():
    files=list((ROOT/"pipeline/15_build_dashboard_payload").glob("*"))
    assert not any(p.name in {"server.py","app.py","api.py","ui.ts"} for p in files)

