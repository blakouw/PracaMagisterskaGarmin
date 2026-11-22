from .helpers12 import full_fixture_records, run_module, setup_root, errors


def test_missing_pws_components_blocks(tmp_path):
    _, weights = full_fixture_records()
    root = setup_root(tmp_path, components=None, weights=weights)
    assert run_module(root) == 1
    assert any(error["code"] == "PWS_COMPONENTS_NOT_FOUND" for error in errors(root)["errors"])
