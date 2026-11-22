from daily_helpers import output_dir, read_json, run_success_fixture

def test_no_derived_metrics(module05, case_root) -> None:
    run_success_fixture(case_root)
    assert module05.execute(root=case_root) == 0
    fields = set(read_json(output_dir(case_root) / "daily_records.json")["fields"])
    forbidden = {"rhr_delta", "ln_rmssd", "acute_load", "chronic_load", "acwr", "readiness", "pws_score", "pws_components", "pws_weights"}
    assert not (fields & forbidden)
