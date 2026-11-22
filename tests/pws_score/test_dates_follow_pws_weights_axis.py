from .helpers12 import component_record, first_record, run_module, setup_root, weight_record, read_json, output


def test_dates_follow_weights_axis(tmp_path):
    components = [component_record("2026-01-01"), component_record("2026-01-02")]
    weights = [weight_record("2026-01-01")]
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    payload = read_json(output(root))
    assert payload["records_count"] == 1
    assert first_record(root)["date"] == "2026-01-01"
