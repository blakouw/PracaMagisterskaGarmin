import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_no_auth_or_token_pipeline_modules_added():
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    ids = {module["id"] for module in registry["modules"]}
    assert "auth_and_profile_api" not in ids
    assert "garmin_token_pipeline" not in ids
