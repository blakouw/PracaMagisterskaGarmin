from activity_helpers import copy_policy, out, read_json, run, write_api
def test_split_normalization(module06, case_root):
 copy_policy(case_root); write_api(case_root, details={"activityId":"200","startTimeLocal":"2026-05-23T08:00:00"}, splits={"splits":[{"distance":1000,"duration":300,"averageSpeed":3.0,"averageHR":140}]})
 assert run(module06,case_root)==0
 split=read_json(out(case_root)/"activities_normalized.json")["activities"][0]["splits"][0]
 assert split["split_index"]==1; assert split["distance_km"]==1.0; assert split["average_speed_kmh"]==10.8
