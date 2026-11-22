from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MODULE_ID = "17_local_api_server"
MISSING_MESSAGE = (
    "Local dashboard snapshot API artifacts do not exist. "
    "Run pipeline/17_local_api_server/run.bat --validate-only first."
)


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_artifacts(root: Path) -> dict[str, Any]:
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    paths = {
        "validation": artifact_dir / "api_startup_validation.json",
        "schema": artifact_dir / "api_contract_schema.json",
        "quality": artifact_dir / "api_quality_report.json",
        "lineage": artifact_dir / "api_lineage.json",
    }
    if not all(path.is_file() for path in paths.values()):
        print(MISSING_MESSAGE)
        raise SystemExit(2)
    return {name: read_json(path) for name, path in paths.items()}


def print_summary(artifacts: dict[str, Any]) -> None:
    validation = artifacts["validation"]
    schema = artifacts["schema"]
    quality = artifacts["quality"]
    snapshot = validation.get("snapshot", {})
    runtime = validation.get("runtime_mode", {})
    checks = validation.get("checks", {})

    print("Local Dashboard Snapshot API")
    print(f"Status: {quality.get('status')}")
    print(f"Local only: {runtime.get('local_only')}")
    print(f"Read only: {runtime.get('read_only')}")
    print(f"Host: {runtime.get('host')}")
    print(f"Port: {runtime.get('port')}")
    print(f"Public exposure approved: {runtime.get('public_exposure_approved')}")
    print("Authentication implemented: false")
    print(f"Current snapshot available: {snapshot.get('available')}")
    print(f"Snapshot id: {snapshot.get('snapshot_id')}")
    print(f"Latest data date: {snapshot.get('latest_data_date')}")
    print(f"Primary score deterministic: {checks.get('primary_score_is_deterministic')}")
    print(
        "Optional assisted available: "
        f"{validation.get('optional_assisted_variant', {}).get('available')}"
    )
    print(f"GET endpoints: {len(schema.get('endpoints', []))}")
    print("Write endpoints: 0")
    print("Pipeline trigger endpoints: 0")
    print("Analytical recomputation: false")
    print("LLM called: false")
    print("Snapshot is loaded at startup. Restart after publishing a new snapshot.")
    print(f"Ready for future UI: {quality.get('ready_for_next_module')}")


def print_endpoints(schema: dict[str, Any]) -> None:
    print("\nGET Endpoints")
    for endpoint in schema.get("endpoints", []):
        print(f"- {endpoint.get('method')} {endpoint.get('path')}: {endpoint.get('response_source')}")


def print_runtime(validation: dict[str, Any]) -> None:
    print("\nRuntime")
    for key, value in validation.get("runtime_mode", {}).items():
        print(f"- {key}: {value}")


def print_validation(validation: dict[str, Any]) -> None:
    print("\nStartup Validation")
    print(f"- validation_status: {validation.get('validation_status')}")
    print(f"- api_ready_to_serve_snapshot: {validation.get('api_ready_to_serve_snapshot')}")
    for key, value in validation.get("checks", {}).items():
        print(f"- {key}: {value}")


def print_lineage(lineage: dict[str, Any]) -> None:
    print("\nLineage")
    print(f"- operation: {lineage.get('runtime_transformation', {}).get('operation')}")
    for source in lineage.get("source_artifacts", []):
        print(f"- {source.get('role')}: {source.get('artifact_path')}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview local API contract artifacts.")
    parser.add_argument("--show-endpoints", action="store_true")
    parser.add_argument("--show-runtime", action="store_true")
    parser.add_argument("--show-validation", action="store_true")
    parser.add_argument("--show-lineage", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts = require_artifacts(root_dir())
    print_summary(artifacts)
    if args.show_endpoints:
        print_endpoints(artifacts["schema"])
    if args.show_runtime:
        print_runtime(artifacts["validation"])
    if args.show_validation:
        print_validation(artifacts["validation"])
    if args.show_lineage:
        print_lineage(artifacts["lineage"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

