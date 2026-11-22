import json
from pathlib import Path


def test_policy_defines_session_rpe_preference_fallback_and_calendar_windows():
    root = Path(__file__).resolve().parents[2]
    policy = json.loads((root / "config/load_metrics_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "load_metrics_policy_v1"
    assert policy["daily_load_source_field"] == "session_rpe_with_active_kcal_fallback"
    assert policy["daily_load_normalized_field"] == "load_value"
    assert policy["daily_load_selection_policy"]["preferred_source"] == "session_rpe"
    assert policy["daily_load_selection_policy"]["fallback_source"] == "active_kcal"
    assert policy["date_axis_policy"]["window_unit"] == "calendar_days"
    assert policy["date_axis_policy"]["missing_calendar_dates_policy"] == "do_not_impute_and_do_not_assume_zero"
    assert policy["ewma_load_metrics"]["acute_ewma"]["alpha"] == 0.25
    assert round(policy["ewma_load_metrics"]["chronic_ewma"]["alpha"], 12) == round(2 / 29, 12)
    assert "readiness" in policy["prohibited_calculations"]
