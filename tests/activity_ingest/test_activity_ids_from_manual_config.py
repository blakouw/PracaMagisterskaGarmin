from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config, write_tokenstore


def test_activity_ids_from_manual_config(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=["200", "100", "bad", ""])
    write_tokenstore(case_root)
    exit_code = run_module(module04, case_root, dependency=True)
    assert exit_code == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    assert manifest["requested_activity_ids"] == ["100", "200"]
    assert manifest["activity_id_sources"] == ["manual_config"]
    assert manifest["status"] == "completed"
