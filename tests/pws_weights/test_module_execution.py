from .helpers11 import component_record, errors, run_module, setup_root


def test_module_execution_on_missing_input_blocks_cleanly(tmp_path):
    root = setup_root(tmp_path, records=None)
    assert run_module(root) == 1
    assert errors(root)["errors"][0]["code"] == "PWS_COMPONENTS_NOT_FOUND"


def test_run_function_execution(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
