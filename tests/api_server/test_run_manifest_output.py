from snapshotapi_fixtures import load_ctx

def test_run_manifest_output(tmp_path, main_module, monkeypatch):
    load_ctx(tmp_path, __import__("api_app"))
    monkeypatch.setattr(main_module, "root_dir", lambda: tmp_path)
    main_module.main(["--validate-only"])
    assert (tmp_path/"data/pipeline/17_local_api_server/run_manifest.json").is_file()
    assert (tmp_path/"data/pipeline/17_local_api_server/run_log.txt").is_file()
    assert (tmp_path/"data/pipeline/17_local_api_server/errors.json").is_file()
