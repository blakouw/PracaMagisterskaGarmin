from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_no_frontend_files_in_module():
    files=[p.suffix for p in (ROOT/"pipeline/17_local_api_server").glob("**/*") if p.is_file()]
    assert ".html" not in files
    assert ".tsx" not in files
    assert ".jsx" not in files
