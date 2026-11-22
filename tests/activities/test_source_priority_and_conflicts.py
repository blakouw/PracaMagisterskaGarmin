from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv, write_api
def test_source_priority_and_conflicts(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(distance="10240")]); write_api(case_root, aid="100", details={"activityId":"100","startTimeLocal":"2026-05-22T07:14:00","distance":9999}, splits=[])
 assert run(module06,case_root)==0
 p=read_json(out(case_root)/"activities_normalized.json"); q=read_json(out(case_root)/"activity_data_quality_report.json")
 assert p["activities"][0]["distance_km"]==10.24; assert q["field_conflicts"]
