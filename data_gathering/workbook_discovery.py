from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "01_find_input_workbook"
CONTRACT_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_RELATIVE_DIR = Path("data/pipeline") / MODULE_ID
WORKBOOK_MANIFEST_NAME = "workbook_manifest.json"
RUN_MANIFEST_NAME = "run_manifest.json"
RUN_LOG_NAME = "run_log.txt"
ERRORS_NAME = "errors.json"
ALLOWED_SELECTION_STRATEGIES = {"first_path_sorted_ascending"}


class ModuleError(Exception):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = context or {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def to_relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def validate_search_directory(root: Path, configured_path: str) -> Path:
    if not isinstance(configured_path, str) or not configured_path.strip():
        raise ModuleError(
            "CONFIG_VALIDATION_ERROR",
            "Each workbook search directory must be a non-empty relative path.",
            {"configured_path": configured_path},
        )
    candidate = Path(configured_path)
    if candidate.is_absolute():
        raise ModuleError(
            "CONFIG_VALIDATION_ERROR",
            "Workbook search directories must not be absolute paths.",
            {"configured_path": configured_path},
        )

    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ModuleError(
            "CONFIG_VALIDATION_ERROR",
            "Workbook search directory points outside the project root.",
            {"configured_path": configured_path},
        )
    return resolved


def load_search_config(root: Path) -> dict[str, Any]:
    config_path = root / "config" / "project_settings.json"
    try:
        settings = read_json(config_path)
    except FileNotFoundError as exc:
        raise ModuleError("CONFIG_READ_ERROR", "config/project_settings.json does not exist.", {}) from exc
    except json.JSONDecodeError as exc:
        raise ModuleError("CONFIG_READ_ERROR", "config/project_settings.json is not valid JSON.", {"error": str(exc)}) from exc

    workbook_config = settings.get("input_workbook")
    if not isinstance(workbook_config, dict):
        raise ModuleError("CONFIG_VALIDATION_ERROR", "Missing input_workbook configuration.", {})

    filename_pattern = workbook_config.get("filename_pattern")
    if not isinstance(filename_pattern, str) or not filename_pattern.strip():
        raise ModuleError("CONFIG_VALIDATION_ERROR", "input_workbook.filename_pattern must be a non-empty string.", {})
    if "/" in filename_pattern or "\\" in filename_pattern:
        raise ModuleError("CONFIG_VALIDATION_ERROR", "input_workbook.filename_pattern must be a filename pattern only.", {})

    search_directories = workbook_config.get("search_directories")
    if not isinstance(search_directories, list) or not search_directories:
        raise ModuleError("CONFIG_VALIDATION_ERROR", "input_workbook.search_directories must be a non-empty list.", {})

    recursive = workbook_config.get("recursive")
    if recursive is not False:
        raise ModuleError("CONFIG_VALIDATION_ERROR", "input_workbook.recursive must be false for module 01.", {})

    selection_strategy = workbook_config.get("selection_strategy")
    if selection_strategy not in ALLOWED_SELECTION_STRATEGIES:
        raise ModuleError(
            "CONFIG_VALIDATION_ERROR",
            "Unsupported input_workbook.selection_strategy.",
            {"selection_strategy": selection_strategy},
        )

    validated_dirs = [validate_search_directory(root, item) for item in search_directories]
    if "data/input" in search_directories:
        (root / "data" / "input").mkdir(parents=True, exist_ok=True)

    return {
        "filename_pattern": filename_pattern,
        "search_directories": search_directories,
        "resolved_search_directories": validated_dirs,
        "recursive": recursive,
        "selection_strategy": selection_strategy,
        "require_exactly_one_match": workbook_config.get("require_exactly_one_match", False),
    }


def collect_candidates(root: Path, search_config: dict[str, Any]) -> list[dict[str, Any]]:
    by_resolved_path: dict[Path, dict[str, Any]] = {}
    pattern = search_config["filename_pattern"]

    for directory in search_config["resolved_search_directories"]:
        if not directory.exists() or not directory.is_dir():
            continue
        for path in directory.glob(pattern):
            if not path.is_file():
                continue
            resolved = path.resolve()
            stat = path.stat()
            by_resolved_path[resolved] = {
                "relative_path": to_relative(root, path),
                "filename": path.name,
                "extension": path.suffix,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "exists": path.exists(),
            }

    return sorted(by_resolved_path.values(), key=lambda item: item["relative_path"])


def build_workbook_manifest(search_config: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    warnings: list[str] = []
    selected = candidates[0] if candidates else None
    domain_status = "found" if selected else "missing"

    if not selected:
        warnings.append("No Garmin workbook matching the configured filename pattern was found.")
    elif len(candidates) > 1:
        warnings.append(
            "Multiple Garmin workbook candidates were found. The selected workbook was chosen using "
            "first_path_sorted_ascending strategy."
        )

    return {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "status": domain_status,
        "search_configuration": {
            "filename_pattern": search_config["filename_pattern"],
            "search_directories": search_config["search_directories"],
            "recursive": search_config["recursive"],
            "selection_strategy": search_config["selection_strategy"],
        },
        "candidates_count": len(candidates),
        "candidates": candidates,
        "selected_workbook": selected,
        "warnings": warnings,
        "ready_for_next_module": selected is not None,
    }


def write_run_log(
    path: Path,
    started_at: str,
    finished_at: str,
    execution_status: str,
    domain_status: str,
    search_config: dict[str, Any] | None,
    candidates_count: int,
    selected_workbook: dict[str, Any] | None,
    warnings: list[str],
) -> None:
    lines = [
        f"module_id={MODULE_ID}",
        f"started_at={started_at}",
        f"execution_status={execution_status}",
        f"domain_status={domain_status}",
    ]
    if search_config is not None:
        lines.extend(
            [
                f"filename_pattern={search_config['filename_pattern']}",
                f"selection_strategy={search_config['selection_strategy']}",
                "search_directories=" + ", ".join(search_config["search_directories"]),
                f"recursive={search_config['recursive']}",
            ]
        )
    lines.append(f"candidates_count={candidates_count}")
    if selected_workbook is None:
        lines.append("selected_workbook=none")
    else:
        lines.append(f"selected_workbook={selected_workbook['relative_path']}")
    for warning in warnings:
        lines.append(f"warning={warning}")
    lines.append("xlsx_contents_read=false")
    lines.append("Workbook contents, sheets, cells and columns were not read.")
    lines.append(f"finished_at={finished_at}")
    lines.append(f"status={execution_status}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(root: Path = ROOT) -> int:
    started_at = now_iso()
    artifact_dir = root / ARTIFACT_RELATIVE_DIR
    artifact_dir.mkdir(parents=True, exist_ok=True)
    workbook_manifest_path = artifact_dir / WORKBOOK_MANIFEST_NAME
    run_manifest_path = artifact_dir / RUN_MANIFEST_NAME
    run_log_path = artifact_dir / RUN_LOG_NAME
    errors_path = artifact_dir / ERRORS_NAME

    generated_artifacts = [
        (ARTIFACT_RELATIVE_DIR / WORKBOOK_MANIFEST_NAME).as_posix(),
        (ARTIFACT_RELATIVE_DIR / RUN_MANIFEST_NAME).as_posix(),
        (ARTIFACT_RELATIVE_DIR / RUN_LOG_NAME).as_posix(),
        (ARTIFACT_RELATIVE_DIR / ERRORS_NAME).as_posix(),
    ]

    search_config: dict[str, Any] | None = None
    candidates_count = 0
    selected_workbook: dict[str, Any] | None = None
    warnings: list[str] = []
    domain_status = "unknown"
    errors: list[dict[str, Any]] = []
    execution_status = "success"

    try:
        search_config = load_search_config(root)
        candidates = collect_candidates(root, search_config)
        workbook_manifest = build_workbook_manifest(search_config, candidates)
        write_json(workbook_manifest_path, workbook_manifest)

        candidates_count = workbook_manifest["candidates_count"]
        selected_workbook = workbook_manifest["selected_workbook"]
        warnings = workbook_manifest["warnings"]
        domain_status = workbook_manifest["status"]
    except ModuleError as exc:
        execution_status = "failed"
        domain_status = "not_evaluated"
        errors.append({"code": exc.code, "message": exc.message, "context": exc.context})
    except Exception as exc:
        execution_status = "failed"
        domain_status = "not_evaluated"
        errors.append({"code": "UNHANDLED_ERROR", "message": str(exc), "context": {}})

    finished_at = now_iso()
    write_json(errors_path, {"module_id": MODULE_ID, "errors": errors})
    write_run_log(
        run_log_path,
        started_at,
        finished_at,
        execution_status,
        domain_status,
        search_config,
        candidates_count,
        selected_workbook,
        warnings,
    )
    write_json(
        run_manifest_path,
        {
            "module_id": MODULE_ID,
            "module_version": CONTRACT_VERSION,
            "started_at": started_at,
            "finished_at": finished_at,
            "execution_status": execution_status,
            "domain_status": domain_status,
            "inputs": [
                "config/project_settings.json"
            ],
            "generated_artifacts": generated_artifacts,
            "log_file": (ARTIFACT_RELATIVE_DIR / RUN_LOG_NAME).as_posix(),
            "errors_file": (ARTIFACT_RELATIVE_DIR / ERRORS_NAME).as_posix(),
        },
    )
    return 0 if execution_status == "success" else 1


def main() -> int:
    return execute(ROOT)


if __name__ == "__main__":
    sys.exit(main())
