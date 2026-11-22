from datetime import datetime, timezone

def test_existing_history_snapshot_is_not_overwritten(tmp_path, snapshot_module):
    hist = tmp_path / "history"
    base = snapshot_module.snapshot_id_from("2026-01-03", datetime(2026, 5, 23, tzinfo=timezone.utc))
    marker = hist / base / "marker.txt"
    marker.parent.mkdir(parents=True)
    marker.write_text("keep", encoding="utf-8")
    sid = snapshot_module.unique_snapshot_id("2026-01-03", datetime(2026, 5, 23, tzinfo=timezone.utc), hist)
    assert sid != base
    assert marker.read_text(encoding="utf-8") == "keep"
