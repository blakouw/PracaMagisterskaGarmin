from .helpers12 import full_fixture_records, run_module, setup_root


def test_no_llm_or_network_calls(monkeypatch, tmp_path):
    def blocked(*args, **kwargs):
        raise AssertionError("network or LLM call attempted")
    monkeypatch.setattr("socket.create_connection", blocked)
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
