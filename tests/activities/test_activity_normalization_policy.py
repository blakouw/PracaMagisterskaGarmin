from activity_helpers import ROOT, read_json
def test_policy_shape():
 p=read_json(ROOT/"config"/"garmin_activity_normalization_v1.json")
 assert p["policy_version"]=="garmin_activity_normalization_v1"; assert p["activity_sources_optional"] is True; assert p["missing_values_policy"]=="preserve_as_null"; assert p["fit_tcx_policy"]["parse_fit"] is False; assert p["fit_tcx_policy"]["parse_tcx"] is False; assert "training_load" in p["prohibited_derived_metrics"]
