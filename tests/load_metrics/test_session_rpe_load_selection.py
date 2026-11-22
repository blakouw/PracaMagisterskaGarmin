from .helpers08 import load_output_records, make_records, run_module, setup_root


def activity(activity_id, date, duration_seconds, rpe):
    return {
        "activity_id": activity_id,
        "date": date,
        "duration_seconds": duration_seconds,
        "perceived_effort_rpe": rpe,
    }


def test_complete_daily_rpe_uses_sum_of_rpe_times_duration_minutes(tmp_path):
    records = make_records([500], start="2026-01-01")
    activities = [
        activity("a", "2026-01-01", 3600, 6),
        activity("b", "2026-01-01", 1800, 4),
    ]
    root = setup_root(tmp_path, records=records, activities=activities)

    assert run_module(root) == 0
    record = load_output_records(root)[0]
    assert record["load_session_rpe"] == 480
    assert record["load_value"] == 480
    assert record["load_active_kcal"] == 500
    assert record["load_source"] == "session_rpe"
    assert record["session_rpe_coverage_complete"] is True


def test_any_missing_rpe_falls_back_for_the_entire_day(tmp_path):
    records = make_records([500], start="2026-01-01")
    activities = [
        activity("a", "2026-01-01", 3600, 6),
        activity("b", "2026-01-01", 1800, None),
    ]
    root = setup_root(tmp_path, records=records, activities=activities)

    assert run_module(root) == 0
    record = load_output_records(root)[0]
    assert record["load_session_rpe"] is None
    assert record["load_value"] == 500
    assert record["load_source"] == "active_kcal_fallback"
    assert record["session_rpe_evaluated_activity_count"] == 1
    assert record["session_rpe_coverage_complete"] is False
