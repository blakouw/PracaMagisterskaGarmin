from helpers07 import setup_root, run_module, output
def test_health_null_preserved(tmp_path):
    root = setup_root(tmp_path, write_activity=False)
    assert run_module(root) == 0
    assert output(root)["records"][0]["steps"] is None
    assert output(root)["records"][0]["sleep_seconds"] is None
