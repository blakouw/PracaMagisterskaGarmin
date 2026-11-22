from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_null_and_negative_active_kcal_block(tmp_path):
    root = setup_root(tmp_path, records=make_records([100, None]))
    assert run_module(root) == 1
    errors = read_json(output(root, "errors.json"))["errors"]
    assert any(error["code"] == "ACTIVE_KCAL_INVALID" for error in errors)

    root2 = setup_root(tmp_path / "negative", records=make_records([100, -1]))
    assert run_module(root2) == 1
    errors2 = read_json(output(root2, "errors.json"))["errors"]
    assert any(error["code"] == "ACTIVE_KCAL_NEGATIVE" for error in errors2)
