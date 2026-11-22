from datetime import datetime, timezone

def test_snapshot_id_unique_suffix(tmp_path, snapshot_module):
    hist = tmp_path / "history"
    base = snapshot_module.snapshot_id_from("2026-01-03", datetime(2026, 5, 23, tzinfo=timezone.utc))
    (hist / base).mkdir(parents=True)
    sid = snapshot_module.unique_snapshot_id("2026-01-03", datetime(2026, 5, 23, tzinfo=timezone.utc), hist)
    assert sid.endswith("_01")
    assert (hist / base).is_dir()
