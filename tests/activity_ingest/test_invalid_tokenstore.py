from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config, write_tokenstore


def test_invalid_tokenstore_is_controlled_skip(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=["100"])
    write_tokenstore(case_root, valid=False)
    exit_code = run_module(module04, case_root, dependency=True)
    assert exit_code == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    errors = read_json(artifact_dir(case_root) / "errors.json")
    assert manifest["status"] == "skipped_missing_credentials"
    assert any(item["code"] == "LOCAL_TOKENSTORE_INVALID" for item in errors["errors"])
