from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config


def test_missing_dependency_is_controlled_skip(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=["100"])
    exit_code = run_module(module04, case_root, dependency=False)
    assert exit_code == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    assert manifest["status"] == "skipped_dependency_unavailable"
    assert manifest["api_called"] is False
    assert manifest["does_not_block_workbook_pipeline"] is True
