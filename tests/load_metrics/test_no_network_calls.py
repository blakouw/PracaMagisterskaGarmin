import socket
from .helpers08 import make_records, run_module, setup_root


def test_no_network_calls(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise AssertionError("network call attempted")

    monkeypatch.setattr(socket, "create_connection", fail)
    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0
