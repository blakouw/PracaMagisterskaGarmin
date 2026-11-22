from daily_helpers import copy_policy, output_dir, read_json, write_trim_artifacts

def test_api_ingest_is_not_consumed(module05, case_root) -> None:
    copy_policy(case_root)
    write_trim_artifacts(case_root, {"Daily_Summary": [{"calendarDate": "2026-01-01", "activeKilocalories": "1"}]})
    api_dir = case_root / "data" / "pipeline" / "04_garmin_activity_ingest"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "activity_ingest_manifest.json").write_text('{"status":"completed"}', encoding="utf-8")
    assert module05.execute(root=case_root) == 0
    log = (output_dir(case_root) / "run_log.txt").read_text(encoding="utf-8")
    assert "garmin_api_artifacts_used=false" in log
