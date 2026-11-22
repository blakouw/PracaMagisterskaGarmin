from activity_ingest_helpers import PartialFailureAdapter, artifact_dir, read_json, run_module, write_config, write_tokenstore


def test_partial_download_failure_continues(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=["100", "200"])
    write_tokenstore(case_root)
    exit_code = run_module(module04, case_root, dependency=True, adapter=PartialFailureAdapter)
    assert exit_code == 0
    base = artifact_dir(case_root)
    manifest = read_json(base / "activity_ingest_manifest.json")
    assert manifest["status"] == "completed_with_failures"
    assert manifest["activities_downloaded_count"] == 2
    assert (base / "activities" / "100" / "activity.fit").is_file()
    assert not (base / "activities" / "200" / "activity.fit").is_file()
    errors = read_json(base / "errors.json")
    assert any(item["code"] == "FIT_DOWNLOAD_FAILED" for item in errors["errors"])
