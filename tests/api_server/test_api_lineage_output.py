from snapshotapi_fixtures import load_ctx

def test_lineage_output(tmp_path, main_module, monkeypatch):
    load_ctx(tmp_path, __import__("api_app"))
    monkeypatch.setattr(main_module, "root_dir", lambda: tmp_path)
    main_module.main(["--validate-only"])
    assert (tmp_path/"data/pipeline/17_local_api_server/api_lineage.json").is_file()
