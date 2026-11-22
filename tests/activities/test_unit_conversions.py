from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_unit_conversions(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(distance="10240", averageSpeed="3.5", duration="3140")]); assert run(module06,case_root)==0
 a=read_json(out(case_root)/"activities_normalized.json")["activities"][0]; q=read_json(out(case_root)/"activity_data_quality_report.json")
 assert a["distance_km"]==10.24; assert a["average_speed_kmh"]==12.6; assert a["duration_seconds"]==3140; assert q["unit_conversions_applied"]["distance_m_to_km_count"]>=1
