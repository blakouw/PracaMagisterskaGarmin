from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "pipeline/18_angular_dashboard_ui/app"


def test_no_external_tracking():
    text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (APP / "src").rglob("*")
        if path.is_file() and not path.name.endswith(".test.tsx") and "test" not in path.parts
    )
    for forbidden in ["gtag", "mixpanel", "segment.com", "google-analytics", "remote font"]:
        assert forbidden not in text
