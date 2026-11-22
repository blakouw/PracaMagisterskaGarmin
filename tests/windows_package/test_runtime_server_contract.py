from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "pipeline/19_packaging_windows/runtime_server.py"


def test_runtime_binds_localhost_and_has_no_public_host_cli():
    text = RUNTIME.read_text(encoding="utf-8")
    assert 'DEFAULT_HOST = "127.0.0.1"' in text
    assert "0.0.0.0" not in text
    assert "--host" not in text
    assert "--port" not in text


def test_runtime_serves_api_and_static_ui_without_vite():
    text = RUNTIME.read_text(encoding="utf-8")
    assert "handle_get" in text
    assert "runtime\" / \"ui" in text
    assert "ThreadingHTTPServer" in text
    assert "vite" not in text.lower()


def test_runtime_rejects_write_methods():
    text = RUNTIME.read_text(encoding="utf-8")
    for method in ["do_POST", "do_PUT", "do_PATCH", "do_DELETE"]:
        assert method in text
    assert "METHOD_NOT_ALLOWED" in text
