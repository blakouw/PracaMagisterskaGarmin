from .helpers11 import component_record, run_module, setup_root


def test_no_llm_or_network_calls(monkeypatch, tmp_path):
    def blocked(*args, **kwargs):
        raise AssertionError("network or LLM call attempted")

    monkeypatch.setattr("socket.create_connection", blocked)
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
