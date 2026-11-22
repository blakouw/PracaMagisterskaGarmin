from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv, write_api
def test_api_enrichment_of_workbook_activity(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(avgPower="")]); write_api(case_root, aid="100", details={"activityId":"100","startTimeLocal":"2026-05-22T07:14:00","avgPower":275}, splits={"splits":[{"distance":1000,"duration":300,"averageSpeed":3.3}]})
 assert run(module06,case_root)==0
 a=read_json(out(case_root)/"activities_normalized.json")["activities"][0]
 assert a["source_presence"]["api_details"] is True; assert a["source_presence"]["api_splits"] is True; assert a["average_power_w"]==275; assert len(a["splits"])==1
