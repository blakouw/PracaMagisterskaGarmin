from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config


def test_manifest_outputs_created_for_skipped_status(module04, case_root) -> None:
    write_config(case_root, enabled=False)
    assert run_module(module04, case_root) == 0
    base = artifact_dir(case_root)
    for filename in ["activity_ingest_manifest.json", "run_manifest.json", "run_log.txt", "errors.json"]:
        assert (base / filename).is_file()
    run_manifest = read_json(base / "run_manifest.json")
    assert run_manifest["domain_status"] == "skipped_disabled"
    assert run_manifest["does_not_block_workbook_pipeline"] is True
