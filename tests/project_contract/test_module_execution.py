import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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


def test_module_00_execution_generates_required_artifacts() -> None:
    result = run_module_00()
    assert result.returncode == 0, result.stdout + result.stderr

    for artifact_name in REQUIRED_ARTIFACTS:
        assert (ARTIFACT_DIR / artifact_name).is_file(), artifact_name

    errors = json.loads((ARTIFACT_DIR / "errors.json").read_text(encoding="utf-8"))
    assert errors == {"module_id": "00_project_contract", "errors": []}

    run_manifest = json.loads((ARTIFACT_DIR / "run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["module_id"] == "00_project_contract"
    assert run_manifest["status"] == "succeeded"
    for artifact_name in REQUIRED_ARTIFACTS:
        assert f"data/pipeline/00_project_contract/{artifact_name}" in run_manifest["generated_artifacts"]

    project_manifest = json.loads((ARTIFACT_DIR / "project_manifest.json").read_text(encoding="utf-8"))
    assert project_manifest["registered_module_count"] == 20
    assert project_manifest["active_implementation_module"] == "00_project_contract"
    assert project_manifest["previous_project_isolation"]["runtime_dependency_allowed"] is False
    assert project_manifest["llm_policy_summary"]["enabled_by_default"] is False
