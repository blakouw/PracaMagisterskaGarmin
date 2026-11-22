from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config, write_tokenstore


def test_successful_mocked_download_writes_all_artifacts(module04, case_root) -> None:
    write_config(case_root, enabled=True, manual_activity_ids=["100"])
    write_tokenstore(case_root)
    exit_code = run_module(module04, case_root, dependency=True)
    assert exit_code == 0
    base = artifact_dir(case_root)
    manifest = read_json(base / "activity_ingest_manifest.json")
    activity_dir = base / "activities" / "100"
    assert manifest["status"] == "completed"
    assert manifest["activities_downloaded_count"] == 1
    assert (activity_dir / "details.json").is_file()
    assert (activity_dir / "splits.json").is_file()
    assert (activity_dir / "activity.fit").read_bytes() == b"FITDATA"
    assert (activity_dir / "activity.tcx").is_file()
    download_manifest = read_json(activity_dir / "download_manifest.json")
    assert download_manifest["status"] == "downloaded"
    assert len(download_manifest["downloaded_artifacts"]) == 4
