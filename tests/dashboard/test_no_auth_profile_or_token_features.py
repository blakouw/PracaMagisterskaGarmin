from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "pipeline/18_angular_dashboard_ui/app/src"


def test_no_auth_profile_or_token_features():
    text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in SRC.rglob("*")
        if path.is_file() and not path.name.endswith(".test.tsx") and "test" not in path.parts
    )
    for forbidden in ["login", "oauth", "tokenstore", "garmin token", "save_profile", "user profile"]:
        assert forbidden not in text
