from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_activity_id_validation(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(activityId="")]); assert run(module06,case_root)==0
 q=read_json(out(case_root)/"activity_data_quality_report.json"); assert q["normalized_activities_count"]==0; assert q["excluded_invalid_records"][0]["reason"]=="missing_activity_id"
