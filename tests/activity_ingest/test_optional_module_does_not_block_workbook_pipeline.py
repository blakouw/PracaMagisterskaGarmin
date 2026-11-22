from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config


def test_skipped_status_does_not_block_workbook_pipeline(module04, case_root) -> None:
    write_config(case_root, enabled=False)
    assert run_module(module04, case_root) == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    assert manifest["does_not_block_workbook_pipeline"] is True
    assert manifest["ready_for_optional_activity_normalization"] is False
