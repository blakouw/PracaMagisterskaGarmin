from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_local_api_proxy_configuration():
    config = (ROOT / "pipeline/18_angular_dashboard_ui/app/vite.config.ts").read_text(encoding="utf-8")
    assert "'/api'" in config
    assert "http://127.0.0.1:8765" in config
    assert "0.0.0.0" not in config
    assert "allow_origins" not in config
    assert "*" not in config.replace("height: 100%", "")
