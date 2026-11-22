from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_workbook_only_normalization(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row()]); assert run(module06,case_root)==0
 p=read_json(out(case_root)/"activities_normalized.json"); a=p["activities"][0]
 assert p["status"]=="normalized_from_workbook_only"; assert a["activity_id"]=="100"; assert a["date"]=="2026-05-22"; assert a["distance_km"]==10.24; assert a["average_speed_kmh"]==12.6; assert a["source_presence"]["workbook"] is True
