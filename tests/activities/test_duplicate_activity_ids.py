from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_duplicate_activity_ids(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(), base_row(distance="999")]); assert run(module06,case_root)==0
 q=read_json(out(case_root)/"activity_data_quality_report.json"); assert q["duplicate_activity_ids"]; assert q["normalized_activities_count"]==0
