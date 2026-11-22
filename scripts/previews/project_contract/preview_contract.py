from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def read_json(relative_path: str) -> Any:
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def section(title: str) -> None:
    print()
    print(title)
    print("=" * len(title))


def main() -> int:
    try:
        project_manifest = read_json("data/pipeline/00_project_contract/project_manifest.json")
        registry = read_json("config/pipeline_modules.json")
        pws_policy = read_json("config/pws_policy_v1.json")
        llm_policy = read_json("config/llm_policy_v1.json")
    except FileNotFoundError as exc:
        print(f"Missing required preview input: {exc.filename}")
        print("Run pipeline\\00_project_contract\\run.bat first.")
        return 1

    modules = registry["modules"]

    section("Project Directories")
    for key, value in project_manifest["roots"].items():
        print(f"{key:16} {value}")
    print(f"{'artifacts':16} {project_manifest['artifact_root']}")
    print(f"{'local_secrets':16} {project_manifest['local_secrets_root']}")

    section("Pipeline Modules")
    print(f"{'Order':5} {'Module':42} {'Status':12} {'Optional'}")
    print("-" * 75)
    for module in modules:
        print(f"{module['order']:>5} {module['id']:<42} {module['status']:<12} {str(module['optional']).lower()}")

    section("Optional Modules")
    for module in modules:
        if module["optional"]:
            print(f"- {module['id']}: {module['responsibility']}")

    section("PWS And LLM Modules")
    for module in modules:
        module_id = module["id"]
        if "pws" in module_id or "llm" in module_id:
            print(f"- {module_id}: {module['name']} ({module['status']})")

    section("PWS Policy")
    print(f"Policy: {pws_policy['policy_version']}")
    print(f"Range: {pws_policy['score_range']['minimum']}..{pws_policy['score_range']['maximum']}")
    print(f"Components: {', '.join(pws_policy['components'].keys())}")
    print(f"Formula: {pws_policy['formula']}")

    section("LLM Weight Influence Limits")
    limits = llm_policy["weight_influence_constraints"]
    print(f"Default LLM mode: {llm_policy['default_mode']}")
    print(f"Maximum adjustment per component: {limits['maximum_adjustment_per_component']}")
    print(f"Maximum total weight shift: {limits['maximum_total_weight_shift']}")
    print(f"Adjustments must sum to zero: {limits['adjustments_must_sum_to_zero']}")
    print(f"Deterministic validation required: {limits['requires_deterministic_validation']}")

    section("Previous Project Isolation")
    isolation = project_manifest["previous_project_isolation"]
    print(f"Runtime dependency allowed: {isolation['runtime_dependency_allowed']}")
    print(f"Reference allowed: {isolation['reference_allowed']}")
    print(f"One-time secret copy allowed: {isolation['one_time_secret_copy_allowed']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
