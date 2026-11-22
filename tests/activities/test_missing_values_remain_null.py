from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_missing_values_remain_null(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(distance="", averageHR="")]); assert run(module06,case_root)==0
 a=read_json(out(case_root)/"activities_normalized.json")["activities"][0]
 assert a["distance_km"] is None; assert a["average_hr_bpm"] is None
