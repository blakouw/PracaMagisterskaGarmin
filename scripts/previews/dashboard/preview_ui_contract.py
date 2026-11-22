from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MODULE_ID = "18_angular_dashboard_ui"
MISSING_MESSAGE = "Local dashboard UI artifacts do not exist. Run pipeline/18_angular_dashboard_ui/build.bat first."


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifacts(root: Path) -> dict[str, Any]:
    artifacts = {
        "schema": root / "pipeline" / MODULE_ID / "ui_contract_schema.json",
        "validation": root / "data" / "pipeline" / MODULE_ID / "ui_validation_report.json",
        "build": root / "data" / "pipeline" / MODULE_ID / "ui_build_manifest.json",
        "quality": root / "data" / "pipeline" / MODULE_ID / "ui_quality_report.json",
        "lineage": root / "data" / "pipeline" / MODULE_ID / "ui_lineage.json",
    }
    if not all(path.is_file() for path in artifacts.values()):
        print(MISSING_MESSAGE)
        raise SystemExit(2)
    return {name: read_json(path) for name, path in artifacts.items()}


def print_summary(artifacts: dict[str, Any]) -> None:
    schema = artifacts["schema"]
    validation = artifacts["validation"]
    build = artifacts["build"]
    quality = artifacts["quality"]
    runtime = validation.get("runtime", {})
    print("Local Dashboard UI")
    print(f"Status: {quality.get('status')}")
    print(f"Stack: {build.get('frontend_stack', {}).get('bundler')}/{build.get('frontend_stack', {}).get('ui_library')}/{build.get('frontend_stack', {}).get('language')}")
    print(f"Host: {runtime.get('frontend_host')}")
    print(f"Port: {runtime.get('frontend_port')}")
    print(f"API proxy target: {runtime.get('api_proxy_target')}")
    print(f"Read only: {runtime.get('read_only')}")
    print(f"Public deployment approved: {runtime.get('public_deployment_approved')}")
    print("Primary score: Deterministic PWS")
    print("Optional assisted score: separate comparison variant")
    print(f"Null values preserved: {quality.get('data_contract', {}).get('null_values_preserved')}")
    print(f"Coverage displayed: {quality.get('data_contract', {}).get('partial_coverage_disclosure_present')}")
    print(f"Direct file reading: {quality.get('forbidden_action_confirmation', {}).get('direct_file_reading')}")
    print(f"Pipeline trigger: {quality.get('forbidden_action_confirmation', {}).get('pipeline_triggering')}")
    print(f"LLM calls: {quality.get('forbidden_action_confirmation', {}).get('llm_calls')}")
    print(f"Auth/profile/token features: {quality.get('forbidden_action_confirmation', {}).get('auth_profile_api_implemented')}")
    print(f"Build status: {build.get('build_status')}")
    print(f"Ready for local use: {quality.get('ready_for_next_module')}")
    print(f"Components: {len(schema.get('required_components', []))}")


def print_components(schema: dict[str, Any]) -> None:
    print("\nComponents")
    for component in schema.get("required_components", []):
        print(f"- {component}")


def print_runtime(validation: dict[str, Any]) -> None:
    print("\nRuntime")
    for key, value in validation.get("runtime", {}).items():
        print(f"- {key}: {value}")


def print_validation(validation: dict[str, Any]) -> None:
    print("\nValidation")
    print(f"- status: {validation.get('validation_status')}")
    for key, value in validation.get("checks", {}).items():
        print(f"- {key}: {value}")


def print_lineage(lineage: dict[str, Any]) -> None:
    print("\nLineage")
    print(f"- source api: {lineage.get('source_api', {}).get('module_id')} {lineage.get('source_api', {}).get('base_path')}")
    for component, source in lineage.get("presentation_mapping", {}).items():
        print(f"- {component}: {source}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview local dashboard UI contract.")
    parser.add_argument("--show-components", action="store_true")
    parser.add_argument("--show-runtime", action="store_true")
    parser.add_argument("--show-validation", action="store_true")
    parser.add_argument("--show-lineage", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts = load_artifacts(root_dir())
    print_summary(artifacts)
    if args.show_components:
        print_components(artifacts["schema"])
    if args.show_runtime:
        print_runtime(artifacts["validation"])
    if args.show_validation:
        print_validation(artifacts["validation"])
    if args.show_lineage:
        print_lineage(artifacts["lineage"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

