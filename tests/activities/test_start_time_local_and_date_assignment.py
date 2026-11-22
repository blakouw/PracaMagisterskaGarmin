from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_start_time_local_and_date_assignment(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(startTimeLocal="2026-05-22T23:30:00+02:00")]); assert run(module06,case_root)==0
 a=read_json(out(case_root)/"activities_normalized.json")["activities"][0]
 assert a["date"]=="2026-05-22"; assert a["start_time_local"]=="2026-05-22T23:30:00+02:00"
