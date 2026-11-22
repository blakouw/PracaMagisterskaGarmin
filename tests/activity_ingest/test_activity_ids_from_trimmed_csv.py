from activity_ingest_helpers import artifact_dir, read_json, run_module, write_activities_csv, write_config, write_tokenstore


def test_activity_ids_from_trimmed_csv(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=[])
    write_activities_csv(case_root, [{"activityId": "300", "activityName": "Run"}, {"activityId": "150", "activityName": "Bike"}])
    write_tokenstore(case_root)
    exit_code = run_module(module04, case_root, dependency=True)
    assert exit_code == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    assert manifest["requested_activity_ids"] == ["150", "300"]
    assert manifest["activity_id_sources"] == ["trimmed_activities_csv"]
