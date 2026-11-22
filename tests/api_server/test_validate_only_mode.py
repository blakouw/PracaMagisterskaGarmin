from snapshotapi_fixtures import load_ctx

def test_validate_only_mode(tmp_path, main_module, monkeypatch):
    load_ctx(tmp_path, __import__("api_app"))
    monkeypatch.setattr(main_module, "root_dir", lambda: tmp_path)
    assert main_module.main(["--validate-only"]) == 0
