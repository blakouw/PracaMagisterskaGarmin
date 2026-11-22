from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config


def test_missing_credentials_is_controlled_skip(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=["100"])
    exit_code = run_module(module04, case_root, dependency=True)
    assert exit_code == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    errors = read_json(artifact_dir(case_root) / "errors.json")
    assert manifest["status"] == "skipped_missing_credentials"
    assert manifest["credentials_checked"] is True
    assert manifest["credentials_valid"] is False
    assert any(item["code"] == "LOCAL_TOKENSTORE_NOT_FOUND" for item in errors["errors"])
