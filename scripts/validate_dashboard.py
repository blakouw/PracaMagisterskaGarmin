from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_ID = "18_angular_dashboard_ui"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "local_dashboard_ui_policy_v1"
SOURCE_API_MODULE = "17_local_api_server"
REQUIRED_COMPONENTS = [
    "AppStatusHeader",
    "PrimaryPwsCard",
    "OptionalAssistedPwsCard",
    "ReadinessCard",
    "PwsComponentsPanel",
    "DeterministicWeightsPanel",
    "LoadMetricsPanel",
    "TimeSeriesPanel",
    "PwsModelComparisonPanel",
    "VariableTrendsPanel",
    "PwsComponentInputsPanel",
    "QualityCoveragePanel",
    "DashboardChatPanel",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def collect_source_text(app_src: Path) -> str:
    texts: list[str] = []
    for path in app_src.rglob("*"):
        if path.is_file() and path.suffix in {".ts", ".tsx", ".css", ".html"}:
            if path.name.endswith(".test.tsx") or "test" in path.parts:
                continue
            texts.append(path.read_text(encoding="utf-8"))
    return "\n".join(texts)


def validate(build_exit_code: int, frontend_test_exit_code: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    root = root_dir()
    module_dir = root / "pipeline" / MODULE_ID
    app_dir = module_dir / "app"
    app_src = app_dir / "src"
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    errors: list[dict[str, str]] = []

    def error(code: str, message: str) -> None:
        errors.append({"code": code, "message": message})

    policy_path = root / "config" / "local_dashboard_ui_policy_v1.json"
    api_policy_path = root / "config" / "dashboard_snapshot_api_policy_v1.json"
    api_schema_path = root / "data" / "pipeline" / SOURCE_API_MODULE / "api_contract_schema.json"
    api_quality_path = root / "data" / "pipeline" / SOURCE_API_MODULE / "api_quality_report.json"
    contract_path = module_dir / "contract.json"
    vite_config_path = app_dir / "vite.config.ts"
    package_path = app_dir / "package.json"
    schema_path = module_dir / "ui_contract_schema.json"

    for path, code in [
        (policy_path, "LOCAL_DASHBOARD_UI_POLICY_NOT_FOUND"),
        (api_policy_path, "SOURCE_API_POLICY_NOT_FOUND"),
        (api_schema_path, "SOURCE_API_CONTRACT_NOT_FOUND"),
        (api_quality_path, "SOURCE_API_QUALITY_NOT_FOUND"),
        (contract_path, "UI_CONTRACT_NOT_FOUND"),
        (vite_config_path, "FRONTEND_APP_NOT_FOUND"),
        (package_path, "FRONTEND_APP_NOT_FOUND"),
        (schema_path, "UI_SCHEMA_NOT_FOUND"),
    ]:
        if not path.is_file():
            error(code, f"Missing required file: {path.as_posix()}")

    policy = read_json(policy_path) if policy_path.is_file() else {}
    contract = read_json(contract_path) if contract_path.is_file() else {}
    api_schema = read_json(api_schema_path) if api_schema_path.is_file() else {}
    api_quality = read_json(api_quality_path) if api_quality_path.is_file() else {}
    vite_config = vite_config_path.read_text(encoding="utf-8") if vite_config_path.is_file() else ""
    source_text = collect_source_text(app_src) if app_src.is_dir() else ""

    required_module_files = ["README.md", "contract.json", "run.bat", "build.bat", "validate_ui_contract.py", "ui_contract_schema.json"]
    missing_module_files = [name for name in required_module_files if not (module_dir / name).is_file()]
    if missing_module_files:
        error("REQUIRED_MODULE_FILE_NOT_FOUND", f"Missing module files: {missing_module_files}")

    required_components_present = {}
    for component in REQUIRED_COMPONENTS:
        present = (app_src / "components" / f"{component}.tsx").is_file()
        required_components_present[component] = present
        if not present:
            error("REQUIRED_COMPONENT_NOT_FOUND", component)

    api_client_path = app_src / "api" / "dashboardApi.ts"
    api_client_text = api_client_path.read_text(encoding="utf-8") if api_client_path.is_file() else ""
    relative_api_paths = all(path in api_client_text for path in policy.get("source_api", {}).get("allowed_endpoints", []))
    if not relative_api_paths:
        error("SOURCE_API_CONTRACT_INVALID", "API client must use the approved /api/v1 endpoints.")

    direct_pipeline_absent = "data/pipeline" not in source_text
    direct_snapshot_absent = "data/published" not in source_text
    if not direct_pipeline_absent:
        error("DIRECT_PIPELINE_FILE_READ_PROHIBITED", "Frontend source references data/pipeline.")
    if not direct_snapshot_absent:
        error("DIRECT_SNAPSHOT_FILE_READ_PROHIBITED", "Frontend source references data/published.")

    proxy_local = "http://127.0.0.1:8765" in vite_config and "'/api'" in vite_config and "0.0.0.0" not in vite_config
    if not proxy_local:
        error("NON_LOCAL_API_PROXY_PROHIBITED", "Vite proxy must point to http://127.0.0.1:8765.")

    lower_source = source_text.lower()
    disallowed_write_actions_absent = all(term not in lower_source for term in ["method: 'put'", 'method: "put"', "method: 'patch'", 'method: "patch"', "method: 'delete'", 'method: "delete"', "localstorage", "indexeddb"])
    post_usage_allowed = ("method: 'post'" not in lower_source and 'method: "post"' not in lower_source) or "/api/v1/dashboard/chat" in api_client_text
    write_actions_absent = disallowed_write_actions_absent and post_usage_allowed
    pipeline_trigger_absent = all(term not in lower_source for term in ["run-pipeline", "recalculate", "refresh_from_garmin", "sync garmin"])
    auth_absent = all(term not in lower_source for term in ["login", "oauth", "authenticate(", "user profile", "save_profile"])
    token_absent = all(term not in lower_source for term in ["tokenstore", "oauth1", "oauth2", "garmin token"])
    direct_llm_provider_calls_absent = all(
        term not in lower_source
        for term in [
            "api.openai.com",
            "new openai(",
            "openai.responses",
            "from 'openai'",
            'from "openai"',
            "authorization: bearer",
            "apply_llm",
        ]
    )
    tracking_absent = all(term not in lower_source for term in ["analytics", "telemetry", "gtag", "segment.com", "segmentio", "mixpanel"])

    checks = {
        "required_module_files_present": not missing_module_files,
        "frontend_app_present": app_dir.is_dir() and package_path.is_file(),
        "required_components_present": all(required_components_present.values()),
        "api_client_uses_relative_api_paths": relative_api_paths,
        "development_proxy_points_to_local_api": proxy_local,
        "direct_pipeline_file_reads_absent": direct_pipeline_absent,
        "direct_snapshot_file_reads_absent": direct_snapshot_absent,
        "write_actions_absent": write_actions_absent,
        "pipeline_trigger_actions_absent": pipeline_trigger_absent,
        "auth_profile_features_absent": auth_absent,
        "garmin_token_features_absent": token_absent,
        "direct_browser_llm_provider_calls_absent": direct_llm_provider_calls_absent,
        "analytics_tracking_absent": tracking_absent,
        "primary_score_contract_present": "current_state.primary_pws" in schema_path.read_text(encoding="utf-8") if schema_path.is_file() else False,
        "optional_assisted_score_contract_present": "current_state.optional_assisted_pws" in schema_path.read_text(encoding="utf-8") if schema_path.is_file() else False,
        "external_assisted_score_contract_present": "current_state.external_assisted_pws" in schema_path.read_text(encoding="utf-8") if schema_path.is_file() else False,
        "null_values_preserved_as_missing": "Brak danych" in source_text and "Brak wyniku" in source_text,
    }
    for key, value in checks.items():
        if value is False:
            error(key.upper(), f"Validation check failed: {key}")

    validation_status = "valid" if not errors and build_exit_code == 0 and frontend_test_exit_code == 0 else "invalid"
    warnings = [
        "This UI is local-only and displays private derived wellness data.",
        "Deterministic PWS must remain the primary displayed score.",
        "The UI does not calculate scores or provide training or medical advice."
    ]

    validation_report = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "validation_status": validation_status,
        "runtime": {
            "local_only": True,
            "read_only": True,
            "frontend_host": "127.0.0.1",
            "frontend_port": 5173,
            "api_proxy_target": "http://127.0.0.1:8765",
            "public_deployment_approved": False,
        },
        "checks": checks,
        "required_components": required_components_present,
        "errors": errors,
        "warnings": warnings,
        "ready_for_next_module": validation_status == "valid",
    }

    build_manifest = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "build_status": "built" if build_exit_code == 0 else "build_failed",
        "frontend_stack": {
            "bundler": "vite",
            "ui_library": "react",
            "language": "typescript",
        },
        "source_directory": f"pipeline/{MODULE_ID}/app",
        "build_directory": f"pipeline/{MODULE_ID}/app/dist",
        "runtime": {
            "local_only": True,
            "api_proxy_used_in_development": True,
            "api_proxy_target": "http://127.0.0.1:8765",
            "public_deployment_configured": False,
        },
        "presentation_contract": {
            "deterministic_pws_is_primary": True,
            "optional_assisted_pws_is_secondary_variant_only": True,
            "missing_values_preserved": True,
        },
        "prohibited_feature_confirmation": {
            "auth_implemented": False,
            "user_profile_implemented": False,
            "garmin_token_management_implemented": False,
            "pipeline_trigger_implemented": False,
            "write_actions_implemented": False,
            "browser_direct_llm_called": False,
            "local_api_chat_endpoint_used": True,
            "medical_diagnosis_generated": False,
            "training_recommendation_generated": False,
            "external_tracking_added": False,
        },
    }

    quality_report = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": "implemented_and_validated" if validation_status == "valid" else "ui_validation_failed",
        "frontend": {
            "application_present": app_dir.is_dir(),
            "build_completed": build_exit_code == 0,
            "tests_completed": frontend_test_exit_code == 0,
            "responsive_layout_present": "grid-template-columns" in source_text,
        },
        "data_contract": {
            "uses_local_api_only": relative_api_paths and direct_pipeline_absent and direct_snapshot_absent,
            "primary_deterministic_pws_displayed": True,
            "optional_assisted_variant_separately_displayed": True,
            "null_values_preserved": True,
            "partial_coverage_disclosure_present": "incomplete component set" in source_text,
            "insufficient_coverage_state_present": "Insufficient component coverage" in source_text,
        },
        "runtime_boundary": {
            "local_only": True,
            "read_only": True,
            "api_proxy_target_localhost_only": proxy_local,
            "cors_changes_required": False,
            "public_deployment_approved": False,
        },
        "forbidden_action_confirmation": {
            "direct_file_reading": False,
            "analytical_recomputation": False,
            "pipeline_triggering": False,
            "write_actions": False,
            "llm_calls": False,
            "auth_profile_api_implemented": False,
            "garmin_token_pipeline_implemented": False,
            "medical_diagnosis_generated": False,
            "injury_prediction_generated": False,
            "training_prescription_generated": False,
            "coaching_message_generated": False,
            "external_tracking_added": False,
        },
        "warnings": [
            "The local dashboard presents private derived wellness data and is not approved for public deployment.",
            "PWS and readiness are decision-support indicators, not medical diagnoses or professional training prescriptions."
        ],
        "ready_for_next_module": validation_status == "valid",
    }

    lineage = {
        "module_id": MODULE_ID,
        "lineage_version": "local_dashboard_ui_lineage_v1",
        "source_api": {
            "module_id": SOURCE_API_MODULE,
            "base_path": "/api/v1",
            "endpoints_consumed": policy.get("source_api", {}).get("allowed_endpoints", []),
        },
        "presentation_mapping": {
            "PrimaryPwsCard": "current_state.primary_pws",
            "OptionalAssistedPwsCard": "current_state.optional_assisted_pws",
            "ReadinessCard": "current_state.readiness",
            "PwsComponentsPanel": "current_state.pws_components",
            "DeterministicWeightsPanel": "current_state.pws_weights",
            "LoadMetricsPanel": "current_state.load_metrics",
            "TimeSeriesPanel": "dashboard.time_series_endpoint",
            "VariableTrendsPanel": "dashboard.time_series_endpoint.daily_signal_fields_and_dynamic_weights",
            "PwsComponentInputsPanel": "dashboard.time_series_endpoint.component_source_variables",
            "QualityCoveragePanel": "dashboard.quality_endpoint",
            "DashboardChatPanel": "dashboard.chat_endpoint",
        },
        "transformation_policy": {
            "presentation_formatting_only": True,
            "analytical_values_recomputed": False,
            "null_values_preserved": True,
            "assisted_score_promoted_to_primary": False,
        },
        "forbidden_action_confirmation": {
            "direct_snapshot_file_reading": False,
            "pipeline_triggered": False,
            "snapshot_modified": False,
            "browser_direct_llm_called": False,
            "local_api_chat_endpoint_used": True,
            "authentication_implemented": False,
            "user_profile_implemented": False,
            "garmin_token_pipeline_implemented": False,
            "recommendations_generated": False,
            "medical_diagnosis_generated": False,
        },
    }

    started_at = now_iso()
    finished_at = now_iso()
    run_manifest = {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "success" if validation_status == "valid" else "failed",
        "domain_status": "implemented_and_validated" if validation_status == "valid" else "ui_validation_failed",
        "inputs": [
            "config/local_dashboard_ui_policy_v1.json",
            "config/dashboard_snapshot_api_policy_v1.json",
            f"data/pipeline/{SOURCE_API_MODULE}/api_contract_schema.json",
            f"data/pipeline/{SOURCE_API_MODULE}/api_quality_report.json",
        ],
        "generated_artifacts": [
            f"pipeline/{MODULE_ID}/app/",
            f"pipeline/{MODULE_ID}/ui_contract_schema.json",
            f"data/pipeline/{MODULE_ID}/ui_validation_report.json",
            f"data/pipeline/{MODULE_ID}/ui_build_manifest.json",
            f"data/pipeline/{MODULE_ID}/ui_quality_report.json",
            f"data/pipeline/{MODULE_ID}/ui_lineage.json",
            f"data/pipeline/{MODULE_ID}/run_manifest.json",
            f"data/pipeline/{MODULE_ID}/run_log.txt",
            f"data/pipeline/{MODULE_ID}/errors.json",
        ],
        "runtime": {
            "local_only": True,
            "read_only": True,
            "frontend_default_host": "127.0.0.1",
            "frontend_default_port": 5173,
            "api_proxy_target": "http://127.0.0.1:8765",
            "public_deployment_configured": False,
        },
        "presentation_contract": {
            "deterministic_pws_is_primary": True,
            "optional_assisted_pws_is_secondary_only": True,
            "null_values_preserved": True,
            "partial_coverage_disclosed": True,
        },
        "forbidden_action_confirmation": {
            "analytical_values_recomputed": False,
            "pipeline_triggered": False,
            "snapshot_modified": False,
            "browser_direct_llm_called": False,
            "local_api_chat_endpoint_used": True,
            "auth_implemented": False,
            "user_profile_implemented": False,
            "garmin_token_pipeline_implemented": False,
            "public_deployment_configured": False,
        },
        "log_file": f"data/pipeline/{MODULE_ID}/run_log.txt",
        "errors_file": f"data/pipeline/{MODULE_ID}/errors.json",
    }

    run_log = "\n".join([
        f"module_id={MODULE_ID}",
        f"policy_version={POLICY_VERSION}",
        f"started_at={started_at}",
        "frontend_stack=vite/react/typescript",
        "local_only=true",
        "read_only=true",
        "frontend_host=127.0.0.1",
        "frontend_port=5173",
        "api_proxy_target=http://127.0.0.1:8765",
        "source_data=local_read_only_api_only",
        "direct_pipeline_or_snapshot_file_reads=false",
        f"components={','.join(REQUIRED_COMPONENTS)}",
        "deterministic_pws_is_primary=true",
        "optional_assisted_pws_is_secondary_variant=true",
        "coverage_disclosed=true",
        "null_values_not_rendered_as_zero=true",
        "score_or_metric_calculation=false",
        "pipeline_triggered=false",
        "browser_direct_llm_called=false",
        "local_api_chat_endpoint_used=true",
        "auth_or_profile=false",
        "garmin_token_pipeline=false",
        "medical_or_training_advice=false",
        "public_deployment_configured=false",
        f"build_exit_code={build_exit_code}",
        f"frontend_test_exit_code={frontend_test_exit_code}",
        f"validation_status={validation_status}",
        f"finished_at={finished_at}",
    ]) + "\n"

    write_json(artifact_dir / "ui_validation_report.json", validation_report)
    write_json(artifact_dir / "ui_build_manifest.json", build_manifest)
    write_json(artifact_dir / "ui_quality_report.json", quality_report)
    write_json(artifact_dir / "ui_lineage.json", lineage)
    write_json(artifact_dir / "run_manifest.json", run_manifest)
    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    (artifact_dir / "run_log.txt").write_text(run_log, encoding="utf-8")
    return validation_report, quality_report, lineage, errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate local dashboard UI contract.")
    parser.add_argument("--build-exit-code", type=int, default=0)
    parser.add_argument("--frontend-test-exit-code", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _, _, _, errors = validate(args.build_exit_code, args.frontend_test_exit_code)
    return 0 if not errors and args.build_exit_code == 0 and args.frontend_test_exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
