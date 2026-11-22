from .helpers11 import component_record, first_record, run_module, setup_root


def test_component_availability_requires_score_and_computed_status(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap=None)])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["component_availability"]["CAP"] is False
    assert record["component_availability"]["LQ"] is True
