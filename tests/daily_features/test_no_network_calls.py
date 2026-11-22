import socket
from helpers07 import setup_root, run_module
def test_no_network_calls(monkeypatch, tmp_path):
    def blocked(*args, **kwargs):
        raise AssertionError("network call attempted")
    monkeypatch.setattr(socket, "create_connection", blocked)
    root = setup_root(tmp_path)
    assert run_module(root) == 0
