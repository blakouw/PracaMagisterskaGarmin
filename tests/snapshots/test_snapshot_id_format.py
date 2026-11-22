from datetime import datetime, timezone

def test_snapshot_id_format(snapshot_module):
    sid = snapshot_module.snapshot_id_from("2026-01-03", datetime(2026, 5, 23, 12, 1, 2, 123456, tzinfo=timezone.utc))
    assert sid == "dashboard_2026-01-03_20260523T120102123456Z"
    assert snapshot_module.is_safe_snapshot_id(sid)
