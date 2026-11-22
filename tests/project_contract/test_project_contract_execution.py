from __future__ import annotations

import json
import os
import subprocess
import sys

from registry_helpers import ROOT


ARTIFACT_DIR = ROOT / "data" / "pipeline" / "00_project_contract"
REQUIRED_ARTIFACTS = [
    "project_manifest.json",
    "pipeline_registry_snapshot.json",
    "run_manifest.json",
    "run_log.txt",
    "errors.json",
]


def run_module_00() -> subprocess.CompletedProcess[str]:
    if os.name == "nt":
        return subprocess.run(
            ["cmd", "/c", "pipeline\\00_project_contract\\run.bat"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    return subprocess.run(
        [sys.executable, "pipeline/00_project_contract/main.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_project_contract_module_executes_without_running_later_modules_or_network_services() -> None:
    result = run_module_00()
    assert result.returncode == 0, result.stdout + result.stderr
    for artifact_name in REQUIRED_ARTIFACTS:
        assert (ARTIFACT_DIR / artifact_name).is_file(), artifact_name
    errors = json.loads((ARTIFACT_DIR / "errors.json").read_text(encoding="utf-8"))
    assert errors == {"module_id": "00_project_contract", "errors": []}
    run_manifest = json.loads((ARTIFACT_DIR / "run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["module_id"] == "00_project_contract"
    assert run_manifest["status"] == "succeeded"
    project_manifest = json.loads((ARTIFACT_DIR / "project_manifest.json").read_text(encoding="utf-8"))
    assert project_manifest["previous_project_isolation"]["runtime_dependency_allowed"] is False
    assert project_manifest["llm_policy_summary"]["enabled_by_default"] is False


def test_project_contract_module_declares_no_private_data_or_external_calls() -> None:
    contract = json.loads((ROOT / "pipeline/00_project_contract/contract.json").read_text(encoding="utf-8"))
    prohibited = set(contract["prohibited_responsibilities"])
    assert "read_garmin_workbook" in prohibited
    assert "fetch_garmin_api_data" in prohibited
    assert "calculate_pws" in prohibited
    assert "call_llm" in prohibited
