import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_no_auth_modules():
    registry=json.loads((ROOT/"config/pipeline_modules.json").read_text())
    ids=[m["id"] for m in registry["modules"]]
    assert "auth_and_profile_api" not in ids
    assert "garmin_token_pipeline" not in ids

