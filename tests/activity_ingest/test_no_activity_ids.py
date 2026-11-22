from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config, write_tokenstore


def test_no_activity_ids_is_controlled_skip(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=[])
    write_tokenstore(case_root)
    assert run_module(module04, case_root, dependency=True) == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    assert manifest["status"] == "skipped_no_activity_ids"
    assert manifest["api_called"] is False
