from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file
from snapshot16_helpers import sha256

def test_sha256_source_hashes(tmp_path, snapshot_module):
    source = write_dashboard_fixture(tmp_path, parquet=True)
    run_module(tmp_path, snapshot_module)
    hashes = read_json_file(current(tmp_path) / "snapshot_source_hashes.json")
    by_name = {f["filename"]: f for f in hashes["files"]}
    assert by_name["dashboard_payload.json"]["source_sha256"] == sha256(source / "dashboard_payload.json")
    assert by_name["dashboard_payload.json"]["hash_match"] is True
