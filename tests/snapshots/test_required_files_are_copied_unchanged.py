from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file
from snapshot16_helpers import sha256

def test_required_files_copied_unchanged(tmp_path, snapshot_module):
    source = write_dashboard_fixture(tmp_path)
    assert run_module(tmp_path, snapshot_module) == "published_without_optional_parquet"
    pub = publication(tmp_path)
    hist = history_dir(tmp_path, pub["snapshot_id"])
    for name in snapshot_module.REQUIRED_SOURCE_FILES:
        assert sha256(source / name) == sha256(hist / name)
