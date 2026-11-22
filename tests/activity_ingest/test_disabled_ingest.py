from activity_ingest_helpers import artifact_dir, read_json, run_module, write_config


def test_disabled_ingest_skips_without_dependency_or_credentials(module04, case_root) -> None:
    write_config(case_root, enabled=False)
    exit_code = run_module(module04, case_root, dependency=False)
    assert exit_code == 0
    manifest = read_json(artifact_dir(case_root) / "activity_ingest_manifest.json")
    run_manifest = read_json(artifact_dir(case_root) / "run_manifest.json")
    assert manifest["status"] == "skipped_disabled"
    assert manifest["credentials_checked"] is False
    assert manifest["api_called"] is False
    assert manifest["ready_for_optional_activity_normalization"] is False
    assert run_manifest["execution_status"] == "success"
