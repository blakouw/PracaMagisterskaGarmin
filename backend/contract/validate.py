from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "00_project_contract"
CONTRACT_VERSION = "1.0.0"
IMPLEMENTED_MODULE_IDS = {"00_project_contract", "01_find_input_workbook", "02_read_xlsx_workbook", "03_trim_workbook", "04_garmin_activity_ingest", "05_normalize_daily_records", "06_normalize_activities", "07_build_daily_features", "08_compute_load_metrics", "09_compute_readiness", "10_compute_pws_components", "11_compute_pws_weights", "12_compute_pws_score", "13_validate_llm_weight_influence", "15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"}
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID
LOG_FILE = ARTIFACT_DIR / "run_log.txt"
ERRORS_FILE = ARTIFACT_DIR / "errors.json"

REQUIRED_DIRECTORIES = [
    "pipeline",
    "tests",
    "visualization",
    "data",
    "data/pipeline",
    "data/local_secrets",
    "config",
    "shared",
]

REQUIRED_CONFIG_FILES = [
    "config/project_settings.json",
    "config/pipeline_modules.json",
    "config/pws_policy_v1.json",
    "config/llm_policy_v1.json",
]

REQUIRED_CONTRACT_FIELDS = [
    "module_id",
    "module_name",
    "version",
    "status",
    "optional",
    "responsibility",
    "depends_on",
    "inputs",
    "outputs",
    "run_command",
    "artifact_directory",
    "test_directory",
    "visualization_directory",
    "prohibited_responsibilities",
    "data_sensitivity",
    "notes",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def gitignore_protects_local_secrets(gitignore_text: str) -> bool:
    normalized = [line.strip().replace("\\", "/") for line in gitignore_text.splitlines()]
    return any(line in {"data/local_secrets/", "data/local_secrets", "data/local_secrets/*"} for line in normalized)


def append_error(errors: list[dict[str, str]], code: str, message: str) -> None:
    errors.append({"code": code, "message": message})


def validate() -> tuple[list[str], list[str], list[str], list[dict[str, str]], dict[str, Any] | None]:
    log: list[str] = []
    errors: list[dict[str, str]] = []
    validated_dirs: list[str] = []
    validated_configs: list[str] = []

    for directory in REQUIRED_DIRECTORIES:
        path = ROOT / directory
        path.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            validated_dirs.append(directory)
            log.append(f"OK directory: {directory}")
        else:
            append_error(errors, "missing_directory", f"Required directory is missing: {directory}")

    settings: dict[str, Any] | None = None
    registry: dict[str, Any] | None = None
    for config_file in REQUIRED_CONFIG_FILES:
        path = ROOT / config_file
        if not path.is_file():
            append_error(errors, "missing_config", f"Required config file is missing: {config_file}")
            continue
        try:
            payload = read_json(path)
        except json.JSONDecodeError as exc:
            append_error(errors, "invalid_json", f"{config_file}: {exc}")
            continue
        validated_configs.append(config_file)
        log.append(f"OK config: {config_file}")
        if config_file.endswith("project_settings.json"):
            settings = payload
        if config_file.endswith("pipeline_modules.json"):
            registry = payload

    if registry is None:
        return log, validated_dirs, validated_configs, errors, None

    modules = registry.get("modules", [])
    if len(modules) != 20:
        append_error(errors, "invalid_registry_count", f"Expected 20 modules, found {len(modules)}")

    for expected_order, module in enumerate(modules):
        module_id = module.get("id", "")
        if module.get("order") != expected_order:
            append_error(errors, "invalid_module_order", f"{module_id} has invalid order {module.get('order')}")
        expected_status = "implemented" if module_id in IMPLEMENTED_MODULE_IDS else "planned"
        if module.get("status") != expected_status:
            append_error(errors, "invalid_module_status", f"{module_id} must have status {expected_status}")

        module_dir = ROOT / "pipeline" / module_id
        if not module_dir.is_dir():
            append_error(errors, "missing_module_directory", f"Missing module directory: pipeline/{module_id}")
            continue

        for filename in ["README.md", "contract.json"]:
            if not (module_dir / filename).is_file():
                append_error(errors, "missing_module_file", f"Missing pipeline/{module_id}/{filename}")

        has_main = (module_dir / "main.py").is_file()
        has_run = (module_dir / "run.bat").is_file()
        if module_id in IMPLEMENTED_MODULE_IDS:
            if not has_main:
                append_error(errors, "missing_main", f"{module_id} must contain main.py")
            if not has_run:
                append_error(errors, "missing_run_bat", f"{module_id} must contain run.bat")
        elif has_main or has_run:
            append_error(errors, "future_module_implemented", f"{module_id} must not contain main.py or run.bat in step 00")

        contract_path = module_dir / "contract.json"
        if contract_path.is_file():
            try:
                contract = read_json(contract_path)
            except json.JSONDecodeError as exc:
                append_error(errors, "invalid_contract_json", f"{rel(contract_path)}: {exc}")
                continue
            missing_fields = [field for field in REQUIRED_CONTRACT_FIELDS if field not in contract]
            if missing_fields:
                append_error(errors, "invalid_contract", f"{rel(contract_path)} missing fields: {missing_fields}")
            if contract.get("module_id") != module_id:
                append_error(errors, "contract_module_mismatch", f"{rel(contract_path)} module_id mismatch")
            if contract.get("status") != module.get("status"):
                append_error(errors, "contract_status_mismatch", f"{rel(contract_path)} status mismatch")

    gitignore_path = ROOT / ".gitignore"
    if not gitignore_path.is_file():
        append_error(errors, "missing_gitignore", ".gitignore is missing")
    elif not gitignore_protects_local_secrets(gitignore_path.read_text(encoding="utf-8")):
        append_error(errors, "local_secrets_not_ignored", "data/local_secrets/ must be ignored by .gitignore")
    else:
        log.append("OK gitignore protects data/local_secrets/")

    if settings is not None and settings.get("previous_project_runtime_dependency_allowed") is not False:
        append_error(errors, "invalid_isolation_policy", "previous_project_runtime_dependency_allowed must be false")
    if settings is not None and settings.get("llm_enabled_by_default") is not False:
        append_error(errors, "invalid_llm_default", "llm_enabled_by_default must be false")

    return log, validated_dirs, validated_configs, errors, registry


def build_project_manifest(settings: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_name": "RepoMagi Garmin Analytics",
        "architecture_mode": settings["architecture_mode"],
        "project_mode": settings["project_mode"],
        "roots": {
            "pipeline": settings["pipeline_root"],
            "tests": settings["tests_root"],
            "visualization": settings["visualization_root"],
            "config": "config",
            "shared": "shared",
            "data": "data",
        },
        "artifact_root": settings["pipeline_output_root"],
        "local_secrets_root": settings["local_secrets_root"],
        "registered_module_count": len(registry["modules"]),
        "active_implementation_module": MODULE_ID,
        "supported_pws_modes": settings["supported_pws_modes"],
        "default_pws_mode": settings["default_pws_mode"],
        "previous_project_isolation": {
            "runtime_dependency_allowed": settings["previous_project_runtime_dependency_allowed"],
            "reference_allowed": settings["previous_project_reference_allowed"],
            "one_time_secret_copy_allowed": settings["previous_project_one_time_secret_copy_allowed"],
        },
        "llm_policy_summary": {
            "enabled_by_default": settings["llm_enabled_by_default"],
            "role": "controlled advisory layer for bounded future PWS weight adjustments only",
            "requires_deterministic_validation": True,
        },
    }


def main() -> int:
    started_at = now_iso()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    generated_artifacts: list[str] = []

    try:
        log, validated_dirs, validated_configs, errors, registry = validate()
        settings = read_json(ROOT / "config" / "project_settings.json") if (ROOT / "config" / "project_settings.json").is_file() else {}

        if registry is not None and settings:
            project_manifest = build_project_manifest(settings, registry)
            project_manifest_path = ARTIFACT_DIR / "project_manifest.json"
            write_json(project_manifest_path, project_manifest)
            generated_artifacts.append(rel(project_manifest_path))

            registry_snapshot_path = ARTIFACT_DIR / "pipeline_registry_snapshot.json"
            write_json(registry_snapshot_path, registry)
            generated_artifacts.append(rel(registry_snapshot_path))

        status = "failed" if errors else "succeeded"
        finished_at = now_iso()

        errors_payload = {"module_id": MODULE_ID, "errors": errors}
        write_json(ERRORS_FILE, errors_payload)
        generated_artifacts.append(rel(ERRORS_FILE))

        log_lines = [
            f"module_id={MODULE_ID}",
            f"started_at={started_at}",
            f"finished_at={finished_at}",
            f"status={status}",
            "",
            *log,
        ]
        if errors:
            log_lines.extend(["", "ERRORS:"])
            log_lines.extend(f"{item['code']}: {item['message']}" for item in errors)
        LOG_FILE.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        generated_artifacts.append(rel(LOG_FILE))

        run_manifest_path = ARTIFACT_DIR / "run_manifest.json"
        run_manifest_relative_path = rel(run_manifest_path)
        if run_manifest_relative_path not in generated_artifacts:
            generated_artifacts.append(run_manifest_relative_path)
        run_manifest = {
            "module_id": MODULE_ID,
            "module_version": CONTRACT_VERSION,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "validated_directories": validated_dirs,
            "validated_configuration_files": validated_configs,
            "generated_artifacts": generated_artifacts,
            "log_file": rel(LOG_FILE),
            "errors_file": rel(ERRORS_FILE),
        }
        write_json(run_manifest_path, run_manifest)

        return 1 if errors else 0
    except Exception as exc:
        finished_at = now_iso()
        error = {"code": "unhandled_exception", "message": str(exc)}
        write_json(ERRORS_FILE, {"module_id": MODULE_ID, "errors": [error]})
        LOG_FILE.write_text(
            f"module_id={MODULE_ID}\nstarted_at={started_at}\nfinished_at={finished_at}\nstatus=failed\n{error['code']}: {error['message']}\n",
            encoding="utf-8",
        )
        write_json(
            ARTIFACT_DIR / "run_manifest.json",
            {
                "module_id": MODULE_ID,
                "module_version": CONTRACT_VERSION,
                "started_at": started_at,
                "finished_at": finished_at,
                "status": "failed",
                "validated_directories": [],
                "validated_configuration_files": [],
                "generated_artifacts": [rel(ERRORS_FILE), rel(LOG_FILE)],
                "log_file": rel(LOG_FILE),
                "errors_file": rel(ERRORS_FILE),
            },
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())


