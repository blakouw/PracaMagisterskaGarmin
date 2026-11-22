from __future__ import annotations

import re
from pathlib import Path

from synthetic_input_factory import MODULE_DIR, MODULE_ID, ROOT, read_project_json


def test_removed_auth_and_token_pipeline_modules_are_not_present() -> None:
    module_ids = {module["id"].lower() for module in read_project_json("config/pipeline_modules.json")["modules"]}
    folder_names = {path.name.lower() for path in (ROOT / "pipeline").iterdir() if path.is_dir()}

    assert "auth_and_profile_api" not in module_ids
    assert "garmin_token_pipeline" not in module_ids
    assert "auth_and_profile_api" not in folder_names
    assert "garmin_token_pipeline" not in folder_names


def test_module_01_contract_prohibits_garmin_api_auth_and_token_responsibilities() -> None:
    contract = read_project_json(f"pipeline/{MODULE_ID}/contract.json")
    prohibited = " ".join(contract["prohibited_responsibilities"]).lower()

    assert "fetch_garmin_api_data" in prohibited
    assert "call_llm" in prohibited
    assert "depend_on_previous_project_runtime" in prohibited
    assert "implement_api_server" in prohibited


def test_module_01_public_files_do_not_implement_auth_or_token_pipeline() -> None:
    active_patterns = [
        re.compile(r"def\s+.*auth", re.IGNORECASE),
        re.compile(r"def\s+.*token", re.IGNORECASE),
        re.compile(r"class\s+.*token", re.IGNORECASE),
        re.compile(r"garmin_token_pipeline", re.IGNORECASE),
        re.compile(r"auth_and_profile_api", re.IGNORECASE),
    ]
    offenders: list[str] = []
    for path in list(MODULE_DIR.glob("*.py")) + list(MODULE_DIR.glob("*.bat")) + [MODULE_DIR / "contract.json"]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in active_patterns):
            offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == []
