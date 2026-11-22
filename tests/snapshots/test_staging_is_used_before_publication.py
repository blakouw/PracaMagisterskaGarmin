from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_staging_is_used_and_cleaned(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    q = read_json_file(tmp_path / "data/pipeline/16_persist_local_snapshot/snapshot_publication_quality_report.json")
    assert q["publication"]["staging_created"] is True
    assert q["publication"]["staging_cleaned"] is True
