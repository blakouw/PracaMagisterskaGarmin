from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_hr_zone_fields(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(hrTimeInZone1="1",hrTimeInZone2="2",hrTimeInZone3="3",hrTimeInZone4="4",hrTimeInZone5="5")]); assert run(module06,case_root)==0
 a=read_json(out(case_root)/"activities_normalized.json")["activities"][0]
 assert [a[f"hr_zone_{i}_seconds"] for i in range(1,6)] == [1,2,3,4,5]
