from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_failed_current_publish_preserves_previous_current(tmp_path, snapshot_module, monkeypatch):
    old = current(tmp_path)
    old.mkdir(parents=True)
    (old / "marker.txt").write_text("old-current", encoding="utf-8")
    write_dashboard_fixture(tmp_path)
    monkeypatch.setenv("SNAPSHOT_SIMULATE_CURRENT_PUBLISH_FAILURE", "1")
    assert run_module(tmp_path, snapshot_module) == "history_snapshot_written_current_publish_failed"
    assert (old / "marker.txt").read_text(encoding="utf-8") == "old-current"
