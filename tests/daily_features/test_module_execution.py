from helpers07 import setup_root, run_module, output
def test_execute_writes_run_manifest(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    m = output(root, "run_manifest.json")
    assert m["execution_status"] == "success"
    assert m["domain_status"] in {"built", "built_without_activity_source"}
