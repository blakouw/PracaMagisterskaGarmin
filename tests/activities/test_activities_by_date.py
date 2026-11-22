from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_activities_by_date(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(activityId="2",startTimeLocal="2026-05-22T09:00:00"),base_row(activityId="1",startTimeLocal="2026-05-22T07:00:00")]); assert run(module06,case_root)==0
 by=read_json(out(case_root)/"activities_by_date.json")
 assert by["dates_count"]==1; assert [x["activity_id"] for x in by["activities_by_date"]["2026-05-22"]]==["1","2"]
