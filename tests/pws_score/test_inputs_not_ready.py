from .helpers12 import full_fixture_records, run_module, setup_root, errors


def test_inputs_not_ready_blocks(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights, weights_ready=False)
    assert run_module(root) == 1
    assert any(error["code"] == "PWS_WEIGHTS_NOT_READY" for error in errors(root)["errors"])
