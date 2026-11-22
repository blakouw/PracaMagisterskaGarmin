from .helpers12 import full_fixture_records, run_module, setup_root, errors


def test_missing_pws_weights_blocks(tmp_path):
    components, _ = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=None)
    assert run_module(root) == 1
    assert any(error["code"] == "PWS_WEIGHTS_NOT_FOUND" for error in errors(root)["errors"])
