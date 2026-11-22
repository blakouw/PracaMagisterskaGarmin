import socket
from .helpers09 import run_module, setup_root, base_record


def test_no_network_calls(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise AssertionError("network call attempted")

    monkeypatch.setattr(socket, "create_connection", fail)
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
