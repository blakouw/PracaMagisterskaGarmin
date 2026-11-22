from .helpers11 import setup_root, run_module, errors


def test_missing_pws_components_blocks(tmp_path):
    root = setup_root(tmp_path, records=None)
    assert run_module(root) == 1
    assert errors(root)["errors"][0]["code"] == "PWS_COMPONENTS_NOT_FOUND"
