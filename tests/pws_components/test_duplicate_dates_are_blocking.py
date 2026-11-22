from .helpers10 import make_load_records, make_readiness_records, output, read_json, run_module, setup_root


def test_duplicate_dates_block(tmp_path):
    load = make_load_records(days=2)
    load[1]["date"] = load[0]["date"]
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records([load[0]]))
    assert run_module(root) == 1
    assert read_json(output(root, "run_manifest.json"))["domain_status"] == "blocked_duplicate_dates"
