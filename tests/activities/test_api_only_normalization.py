from activity_helpers import copy_policy, out, read_json, run, write_api
def test_api_only_normalization(module06, case_root):
 copy_policy(case_root); write_api(case_root, details={"activityId":"200","activityName":"API Ride","activityType":"cycling","startTimeLocal":"2026-05-23T08:00:00","distance":5000,"duration":1000}, splits=[])
 assert run(module06,case_root)==0
 p=read_json(out(case_root)/"activities_normalized.json"); a=p["activities"][0]
 assert p["status"]=="normalized_from_api_only"; assert a["activity_id"]=="200"; assert a["date"]=="2026-05-23"; assert a["source_presence"]["api_details"] is True
