import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def test_policy_shape():
    p = json.loads((ROOT / "config/daily_features_policy_v1.json").read_text(encoding="utf-8"))
    assert p["policy_version"] == "daily_features_policy_v1"
    assert p["primary_source_module"] == "05_normalize_daily_records"
    assert p["optional_activity_source_module"] == "06_normalize_activities"
    assert p["row_creation_rule"] == "one_feature_row_per_daily_record_date_only"
    assert p["missing_health_values_policy"] == "preserve_as_null"
    assert "activity_total_distance_km" in p["activity_daily_aggregations"]
    assert "acwr" in p["prohibited_derived_metrics"]
