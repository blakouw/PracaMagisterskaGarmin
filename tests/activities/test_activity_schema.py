from activity_helpers import copy_policy, out, read_json, run
def test_activity_schema(module06, case_root):
 copy_policy(case_root); run(module06,case_root); s=read_json(out(case_root)/"activity_schema.json")
 assert s["primary_key"]=="activity_id"; assert s["date_grouping_field"]=="date"; assert "training_load" in s["excluded_derived_fields"]
