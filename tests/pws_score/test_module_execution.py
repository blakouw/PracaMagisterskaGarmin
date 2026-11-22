from .helpers12 import errors, full_fixture_records, run_module, setup_root


def test_module_execution_missing_input_blocks(tmp_path):
    components, _ = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=None)
    assert run_module(root) == 1
    assert any(error["code"] == "PWS_WEIGHTS_NOT_FOUND" for error in errors(root)["errors"])


def test_module_execution_success(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
