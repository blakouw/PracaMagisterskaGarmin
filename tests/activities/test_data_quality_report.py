from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv
def test_data_quality_report(module06, case_root):
 copy_policy(case_root); write_activities_csv(case_root,[base_row(avgPower="")]); run(module06,case_root); q=read_json(out(case_root)/"activity_data_quality_report.json")
 assert q["field_coverage"]["average_power_w"]["missing_count"]==1; assert q["raw_artifact_handling"]["fit_tcx_referenced_only"] is True
