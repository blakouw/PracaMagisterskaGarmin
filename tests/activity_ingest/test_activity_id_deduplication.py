from activity_ingest_helpers import artifact_dir, read_json, run_module, write_activities_csv, write_config, write_tokenstore


def test_activity_id_deduplication_and_sorting(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=["20", "10", "20", "abc"])
    write_activities_csv(case_root, [{"activityId": "10", "activityName": "A"}, {"activityId": "30", "activityName": "B"}, {"activityId": "", "activityName": "bad"}])
    write_tokenstore(case_root)
    exit_code = run_module(module04, case_root, dependency=True)
    assert exit_code == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    assert manifest["requested_activity_ids"] == ["10", "20", "30"]
    assert set(manifest["activity_id_sources"]) == {"manual_config", "trimmed_activities_csv"}
    errors = read_json(artifact_dir(case_root) / "errors.json")
    assert any(item["code"] == "ACTIVITY_ID_INVALID" for item in errors["errors"])
