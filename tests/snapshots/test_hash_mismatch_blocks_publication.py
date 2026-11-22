from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_hash_mismatch_blocks_publication(tmp_path, snapshot_module, monkeypatch):
    write_dashboard_fixture(tmp_path)
    def fake_report(*args, **kwargs):
        return {"files": [{"filename": "dashboard_payload.json", "required": True, "hash_match": False}], "all_required_hashes_verified": False, "all_present_optional_hashes_verified": True}
    monkeypatch.setattr(snapshot_module, "build_hash_report", fake_report)
    assert run_module(tmp_path, snapshot_module) == "blocked_snapshot_hash_verification_failed"
    assert not (tmp_path / "data/published/dashboard_snapshots/current").exists()
