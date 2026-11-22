from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_module_execution_on_fixture(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, parquet=True, assisted_available=True, primary_score=75.0)
    assert run_module(tmp_path, snapshot_module) == "published"
    for name in ["snapshot_publication.json", "snapshot_publication_schema.json", "snapshot_publication_quality_report.json", "snapshot_publication_lineage.json", "run_manifest.json", "run_log.txt", "errors.json"]:
        assert (tmp_path / "data/pipeline/16_persist_local_snapshot" / name).is_file(), name
