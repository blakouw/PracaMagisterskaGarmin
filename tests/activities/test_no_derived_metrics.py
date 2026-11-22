from activity_helpers import copy_policy, out, read_json, run

def test_no_derived_metrics_in_normalized_records(module06, case_root):
    copy_policy(case_root)
    run(module06, case_root)
    payload = read_json(out(case_root) / "activities_normalized.json")
    forbidden = {"training_load", "efficiency_score", "capacity_score", "acute_load", "chronic_load", "acwr", "monotony", "strain", "readiness", "pws_score"}
    assert forbidden.isdisjoint(set(payload["fields"]))
    assert not payload["activities"]
