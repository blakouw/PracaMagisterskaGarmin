from activity_helpers import copy_policy, out, read_json, run
def test_empty_sources_are_valid(module06, case_root):
 copy_policy(case_root); assert run(module06,case_root)==0
 p=read_json(out(case_root)/"activities_normalized.json"); q=read_json(out(case_root)/"activity_data_quality_report.json")
 assert p["status"]=="normalized_empty_no_activity_sources"; assert p["activities_count"]==0; assert p["ready_for_next_module"] is True; assert q["ready_for_next_module"] is True
