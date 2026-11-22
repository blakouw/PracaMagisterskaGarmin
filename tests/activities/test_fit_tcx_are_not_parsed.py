from activity_helpers import copy_policy, out, read_json, run, write_api
def test_fit_tcx_are_not_parsed(module06, case_root):
 copy_policy(case_root); write_api(case_root, details={"activityId":"200","startTimeLocal":"2026-05-23T08:00:00"}, splits=[])
 assert run(module06,case_root)==0
 a=read_json(out(case_root)/"activities_normalized.json")["activities"][0]; q=read_json(out(case_root)/"activity_data_quality_report.json")
 assert a["source_presence"]["fit_file"] is True; assert a["api_artifacts"]["fit_file_path"].endswith("activity.fit"); assert q["raw_artifact_handling"]["fit_files_parsed"] is False; assert q["raw_artifact_handling"]["tcx_files_parsed"] is False
