from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "19_packaging_windows"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "windows_packaging_policy_v1"
PACKAGE_NAME = "PersonalWellnessDashboard"
PACKAGE_DIR_NAME = f"{PACKAGE_NAME}_{MODULE_VERSION}_portable"
ZIP_NAME = f"{PACKAGE_DIR_NAME}.zip"
HOST = "127.0.0.1"
PORT = 8765


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def artifact_dir(root: Path) -> Path:
    return root / "data" / "pipeline" / MODULE_ID


def release_root(root: Path) -> Path:
    return root / "release" / "windows"


def package_dir(root: Path) -> Path:
    return release_root(root) / PACKAGE_DIR_NAME


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def run_command(command: list[str], root: Path, cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(command, cwd=str(cwd or root), capture_output=True, text=True, shell=False)
    return proc.returncode, proc.stdout[-4000:], proc.stderr[-4000:]


def validate_policy(root: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    path = root / "config" / "windows_packaging_policy_v1.json"
    if not path.is_file():
        return [{"code": "WINDOWS_PACKAGING_POLICY_NOT_FOUND", "message": "Packaging policy is missing."}]
    try:
        policy = read_json(path)
    except json.JSONDecodeError:
        return [{"code": "WINDOWS_PACKAGING_POLICY_INVALID", "message": "Packaging policy JSON is invalid."}]
    runtime = policy.get("runtime", {})
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append({"code": "WINDOWS_PACKAGING_POLICY_INVALID", "message": "Invalid policy version."})
    if runtime.get("host") != HOST or runtime.get("host_override_allowed") is not False:
        errors.append({"code": "PUBLIC_HOST_PROHIBITED", "message": "Packaged runtime must bind only to 127.0.0.1."})
    if runtime.get("port") != PORT or runtime.get("port_override_allowed") is not False:
        errors.append({"code": "PACKAGE_PORT_OVERRIDE_PROHIBITED", "message": "Packaged runtime port override is prohibited."})
    if runtime.get("public_deployment_approved") is not False or runtime.get("lan_exposure_approved") is not False:
        errors.append({"code": "PUBLIC_DEPLOYMENT_PROHIBITED", "message": "Packaging policy must not approve public or LAN exposure."})
    if runtime.get("vite_dev_server_allowed_in_packaged_runtime") is not False:
        errors.append({"code": "VITE_DEV_SERVER_RUNTIME_PROHIBITED", "message": "Vite dev server is prohibited in packaged runtime."})
    return errors


def validate_registry(root: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    registry = read_json(root / "config" / "pipeline_modules.json")
    modules = {item["id"]: item for item in registry.get("modules", [])}
    module = modules.get(MODULE_ID)
    if module is None:
        errors.append({"code": "WINDOWS_PACKAGING_MODULE_NOT_REGISTERED", "message": "19_packaging_windows is not registered."})
    for required in ["16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui"]:
        if required not in modules:
            errors.append({"code": "REQUIRED_UPSTREAM_MODULE_MISSING", "message": f"Required upstream module missing: {required}"})
    for removed in ["auth_and_profile_api", "garmin_token_pipeline"]:
        if removed in modules:
            errors.append({"code": "REMOVED_MODULE_RESTORED", "message": f"Removed module is present: {removed}"})
    return module, errors


def check_inputs(root: Path) -> list[dict[str, str]]:
    required = [
        "pipeline/17_local_api_server/api_app.py",
        "pipeline/17_local_api_server/contract.json",
        "data/pipeline/17_local_api_server/api_contract_schema.json",
        "data/pipeline/17_local_api_server/api_quality_report.json",
        "pipeline/18_angular_dashboard_ui/app/package.json",
        "pipeline/18_angular_dashboard_ui/build.bat",
        "pipeline/18_angular_dashboard_ui/contract.json",
        "pipeline/18_angular_dashboard_ui/ui_contract_schema.json",
        "data/pipeline/18_angular_dashboard_ui/ui_build_manifest.json",
        "data/pipeline/18_angular_dashboard_ui/ui_quality_report.json",
    ]
    errors = []
    for item in required:
        if not (root / item).exists():
            errors.append({"code": "WINDOWS_PACKAGING_REQUIRED_INPUT_MISSING", "message": f"Missing input: {item}"})
    return errors


def build_ui(root: Path) -> tuple[int, str, str]:
    return run_command([str(root / "pipeline" / "18_angular_dashboard_ui" / "build.bat")], root)


def copy_tree_clean(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prepare_release_tree(root: Path, started_at: str) -> dict[str, Any]:
    pkg = package_dir(root)
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True, exist_ok=True)

    copy_tree_clean(root / "pipeline" / "18_angular_dashboard_ui" / "app" / "dist", pkg / "runtime" / "ui")
    (pkg / "config").mkdir(parents=True, exist_ok=True)
    for config_file in [
        "windows_packaging_policy_v1.json",
        "dashboard_snapshot_api_policy_v1.json",
        "dashboard_snapshot_policy_v1.json",
        "local_dashboard_ui_policy_v1.json",
    ]:
        shutil.copy2(root / "config" / config_file, pkg / "config" / config_file)
    (pkg / "runtime" / "config").mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "config" / "windows_packaging_policy_v1.json", pkg / "runtime" / "config" / "packaged_runtime_policy.json")

    placeholder = pkg / "data" / "published" / "dashboard_snapshots" / "current" / "PLACE_CURRENT_SNAPSHOT_HERE.txt"
    write_text_file(
        placeholder,
        "Place the published current dashboard snapshot files in this directory before starting the packaged app.\n"
        "Required runtime files are defined by config/dashboard_snapshot_api_policy_v1.json.\n"
        "The Windows package intentionally does not include private snapshot data.\n",
    )
    write_text_file(pkg / "logs" / ".gitkeep", "")
    write_text_file(
        pkg / "README.txt",
        "Personal Wellness Dashboard portable Windows package\n\n"
        "This package is local-only and read-only. It starts a local dashboard runtime on http://127.0.0.1:8765/.\n"
        "It does not include private Garmin data, snapshots, tokens or secrets.\n\n"
        "Before first use, copy an already published current snapshot into:\n"
        "data\\published\\dashboard_snapshots\\current\\\n\n"
        "Start the app with START_DASHBOARD.bat or PersonalWellnessDashboard.exe.\n"
        "This package does not sync Garmin data, run the analytical pipeline, call LLMs, implement authentication, "
        "generate medical diagnoses, predict injuries or generate training prescriptions.\n",
    )
    write_text_file(
        pkg / "START_DASHBOARD.bat",
        "@echo off\r\n"
        "setlocal\r\n"
        "set \"SCRIPT_DIR=%~dp0\"\r\n"
        "cd /d \"%SCRIPT_DIR%\"\r\n"
        "PersonalWellnessDashboard.exe %*\r\n"
        "exit /b %ERRORLEVEL%\r\n",
    )
    return {
        "package_directory": relative(root, pkg),
        "prepared_at": started_at,
        "ui_assets_directory": relative(root, pkg / "runtime" / "ui"),
        "snapshot_placeholder": relative(root, placeholder),
    }


def run_pyinstaller(root: Path) -> tuple[int, str, str]:
    dist = release_root(root) / "_pyinstaller_dist"
    work = root / "build" / MODULE_ID
    spec = work
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        PACKAGE_NAME,
        "--distpath",
        str(dist),
        "--workpath",
        str(work),
        "--specpath",
        str(spec),
        "--paths",
        str(root / "pipeline" / "17_local_api_server"),
        str(root / "pipeline" / MODULE_ID / "runtime_server.py"),
    ]
    return run_command(command, root)


def install_executable(root: Path) -> Path:
    source = release_root(root) / "_pyinstaller_dist" / f"{PACKAGE_NAME}.exe"
    target = package_dir(root) / f"{PACKAGE_NAME}.exe"
    if not source.is_file():
        raise FileNotFoundError("PyInstaller did not produce the runtime executable.")
    shutil.copy2(source, target)
    return target


def iter_package_files(pkg: Path) -> list[Path]:
    return sorted(path for path in pkg.rglob("*") if path.is_file())


def integrity_report(root: Path) -> dict[str, Any]:
    pkg = package_dir(root)
    files = []
    for path in iter_package_files(pkg):
        rel = path.relative_to(pkg).as_posix()
        files.append({"path": rel, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        "module_id": MODULE_ID,
        "integrity_version": "windows_package_integrity_v1",
        "algorithm": "sha256",
        "package_directory": relative(root, pkg),
        "files_count": len(files),
        "files": files,
    }


def privacy_audit(root: Path) -> dict[str, Any]:
    pkg = package_dir(root)
    file_names = [path.relative_to(pkg).as_posix() for path in iter_package_files(pkg)]
    forbidden_suffixes = (".fit", ".tcx", ".xlsx", ".parquet")
    forbidden_hits = [name for name in file_names if name.lower().endswith(forbidden_suffixes)]
    snapshot_payload_hits = [name for name in file_names if name.startswith("data/published/dashboard_snapshots/current/") and not name.endswith("PLACE_CURRENT_SNAPSHOT_HERE.txt")]
    secret_name_hits = [name for name in file_names if any(token in name.lower() for token in ["oauth", "tokenstore", "secret", "credential"])]
    findings = []
    for name in forbidden_hits + snapshot_payload_hits + secret_name_hits:
        findings.append({"type": "forbidden_packaged_file", "path": name})
    return {
        "module_id": MODULE_ID,
        "audit_version": "windows_package_privacy_audit_v1",
        "status": "passed" if not findings else "failed",
        "private_snapshots_packaged": bool(snapshot_payload_hits),
        "tokens_or_secrets_packaged": bool(secret_name_hits),
        "raw_garmin_files_packaged": bool(forbidden_hits),
        "vite_dev_server_packaged_as_runtime": False,
        "public_host_enabled": False,
        "telemetry_or_tracking_enabled": False,
        "findings": findings,
    }


def package_manifest(root: Path, exe_path: Path, release_meta: dict[str, Any], zip_path: Path | None) -> dict[str, Any]:
    pkg = package_dir(root)
    return {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "package_name": PACKAGE_NAME,
        "package_version": MODULE_VERSION,
        "package_type": "portable_windows_bundle",
        "package_directory": relative(root, pkg),
        "zip_path": relative(root, zip_path) if zip_path else None,
        "executable": exe_path.relative_to(pkg).as_posix(),
        "runtime": {
            "host": HOST,
            "port": PORT,
            "local_only": True,
            "public_exposure_approved": False,
            "serves_static_ui": True,
            "serves_api_v1": True,
            "uses_vite_dev_server": False,
        },
        "data_policy": {
            "current_snapshot_packaged": False,
            "current_snapshot_expected_runtime_directory": "data/published/dashboard_snapshots/current",
            "tokens_or_secrets_packaged": False,
            "raw_garmin_exports_packaged": False,
        },
        "source_inputs": [
            "pipeline/17_local_api_server/api_app.py",
            "pipeline/18_angular_dashboard_ui/app/dist",
            "config/dashboard_snapshot_api_policy_v1.json",
            "config/dashboard_snapshot_policy_v1.json",
            "config/windows_packaging_policy_v1.json",
        ],
        "release_tree": release_meta,
        "forbidden_action_confirmation": {
            "pipeline_triggered": False,
            "garmin_sync_started": False,
            "llm_called": False,
            "auth_implemented": False,
            "garmin_token_pipeline_implemented": False,
            "public_deployment_implemented": False,
            "medical_diagnosis_generated": False,
            "training_prescription_generated": False,
        },
    }


def create_zip(root: Path) -> Path:
    pkg = package_dir(root)
    zip_path = release_root(root) / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_package_files(pkg):
            archive.write(path, arcname=f"{PACKAGE_DIR_NAME}/{path.relative_to(pkg).as_posix()}")
    return zip_path


def write_release_manifests(root: Path, manifest: dict[str, Any], integrity: dict[str, Any], privacy: dict[str, Any]) -> None:
    manifests_dir = package_dir(root) / "manifests"
    write_json(manifests_dir / "windows_package_manifest.json", manifest)
    write_json(manifests_dir / "windows_package_integrity.json", integrity)
    write_json(manifests_dir / "windows_package_privacy_audit.json", privacy)


def write_module_artifacts(root: Path, started_at: str, finished_at: str, status: str, errors: list[dict[str, Any]], manifest: dict[str, Any] | None, integrity: dict[str, Any] | None, privacy: dict[str, Any] | None, build_info: dict[str, Any]) -> None:
    out = artifact_dir(root)
    out.mkdir(parents=True, exist_ok=True)
    if manifest:
        write_json(out / "windows_package_manifest.json", manifest)
    if integrity:
        write_json(out / "windows_package_integrity.json", integrity)
    if privacy:
        write_json(out / "windows_package_privacy_audit.json", privacy)
    quality = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": "ready_portable_windows_package" if status == "success" else "packaging_failed",
        "ui_build": build_info.get("ui_build"),
        "pyinstaller": build_info.get("pyinstaller"),
        "privacy": {
            "private_snapshots_packaged": False if privacy is None else privacy.get("private_snapshots_packaged"),
            "tokens_or_secrets_packaged": False if privacy is None else privacy.get("tokens_or_secrets_packaged"),
            "raw_garmin_files_packaged": False if privacy is None else privacy.get("raw_garmin_files_packaged"),
        },
        "runtime": {"host": HOST, "port": PORT, "local_only": True, "uses_vite_dev_server": False, "public_exposure_approved": False},
        "ready_for_local_use": status == "success",
    }
    lineage = {
        "module_id": MODULE_ID,
        "lineage_version": "windows_packaging_lineage_v1",
        "source_modules": [
            {"module_id": "17_local_api_server", "role": "local_readonly_api_runtime"},
            {"module_id": "18_angular_dashboard_ui", "role": "production_static_ui_assets"},
        ],
        "runtime_flow": [
            "start_packaged_executable",
            "bind_to_127_0_0_1_8765",
            "load_current_snapshot_from_package_data_directory",
            "serve_api_v1_readonly_endpoints",
            "serve_static_ui_assets",
            "open_local_browser",
        ],
        "forbidden_action_confirmation": {
            "analytical_pipeline_triggered": False,
            "snapshot_modified": False,
            "garmin_data_downloaded": False,
            "llm_called": False,
            "auth_profile_api_implemented": False,
            "garmin_token_pipeline_implemented": False,
            "public_deployment_implemented": False,
        },
    }
    run_manifest = {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": status,
        "domain_status": quality["status"],
        "inputs": [
            "config/windows_packaging_policy_v1.json",
            "pipeline/17_local_api_server/api_app.py",
            "pipeline/18_angular_dashboard_ui/app/dist",
            "pipeline/18_angular_dashboard_ui/build.bat",
        ],
        "generated_artifacts": [
            f"data/pipeline/{MODULE_ID}/windows_package_manifest.json",
            f"data/pipeline/{MODULE_ID}/windows_package_integrity.json",
            f"data/pipeline/{MODULE_ID}/windows_package_privacy_audit.json",
            f"data/pipeline/{MODULE_ID}/windows_package_quality_report.json",
            f"data/pipeline/{MODULE_ID}/windows_package_lineage.json",
            f"data/pipeline/{MODULE_ID}/run_manifest.json",
            f"data/pipeline/{MODULE_ID}/run_log.txt",
            f"data/pipeline/{MODULE_ID}/errors.json",
        ],
        "runtime": {"host": HOST, "port": PORT, "local_only": True, "public_exposure_approved": False},
        "scope_confirmation": {
            "private_snapshots_packaged": False,
            "tokens_or_secrets_packaged": False,
            "raw_garmin_exports_packaged": False,
            "vite_dev_server_used_as_runtime": False,
            "pipeline_triggered": False,
            "garmin_api_called": False,
            "llm_called": False,
        },
        "log_file": f"data/pipeline/{MODULE_ID}/run_log.txt",
        "errors_file": f"data/pipeline/{MODULE_ID}/errors.json",
    }
    write_json(out / "windows_package_quality_report.json", quality)
    write_json(out / "windows_package_lineage.json", lineage)
    write_json(out / "run_manifest.json", run_manifest)
    write_json(out / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    lines = [
        f"module_id={MODULE_ID}",
        f"policy_version={POLICY_VERSION}",
        f"started_at={started_at}",
        f"finished_at={finished_at}",
        f"status={status}",
        "packaged_runtime_host=127.0.0.1",
        "packaged_runtime_port=8765",
        "public_exposure_approved=false",
        "vite_dev_server_runtime=false",
        "production_ui_build_included=true",
        "current_snapshot_packaged=false",
        "tokens_or_secrets_packaged=false",
        "raw_garmin_exports_packaged=false",
        "pipeline_triggered=false",
        "garmin_api_called=false",
        "llm_called=false",
        "auth_profile_api_implemented=false",
        "garmin_token_pipeline_implemented=false",
    ]
    if manifest:
        lines.append(f"package_directory={manifest['package_directory']}")
        lines.append(f"zip_path={manifest['zip_path']}")
    if errors:
        lines.append("errors:")
        lines.extend(f"{item['code']}: {item['message']}" for item in errors)
    (out / "run_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the portable Windows dashboard package.")
    parser.add_argument("--skip-ui-build", action="store_true", help="Use existing UI dist instead of running the UI build script.")
    parser.add_argument("--no-zip", action="store_true", help="Do not create the portable zip archive.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    root = root_dir()
    started_at = now_iso()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    errors: list[dict[str, Any]] = []
    manifest: dict[str, Any] | None = None
    integrity: dict[str, Any] | None = None
    privacy: dict[str, Any] | None = None
    build_info: dict[str, Any] = {}

    errors.extend(validate_policy(root))
    _, registry_errors = validate_registry(root)
    errors.extend(registry_errors)
    errors.extend(check_inputs(root))
    if errors:
        write_module_artifacts(root, started_at, now_iso(), "failed", errors, manifest, integrity, privacy, build_info)
        return 1

    if not args.skip_ui_build:
        ui_code, ui_out, ui_err = build_ui(root)
        build_info["ui_build"] = {"executed": True, "exit_code": ui_code}
        if ui_code != 0:
            errors.append({"code": "UI_PRODUCTION_BUILD_FAILED", "message": "UI production build failed."})
            write_module_artifacts(root, started_at, now_iso(), "failed", errors, manifest, integrity, privacy, build_info)
            return 1
    else:
        build_info["ui_build"] = {"executed": False, "exit_code": None}
    if not (root / "pipeline" / "18_angular_dashboard_ui" / "app" / "dist" / "index.html").is_file():
        errors.append({"code": "UI_PRODUCTION_DIST_MISSING", "message": "UI production dist is missing."})
        write_module_artifacts(root, started_at, now_iso(), "failed", errors, manifest, integrity, privacy, build_info)
        return 1

    release_meta = prepare_release_tree(root, started_at)
    py_code, py_out, py_err = run_pyinstaller(root)
    build_info["pyinstaller"] = {"executed": True, "exit_code": py_code}
    if py_code != 0:
        errors.append({"code": "PYINSTALLER_BUILD_FAILED", "message": "PyInstaller did not complete successfully."})
        write_module_artifacts(root, started_at, now_iso(), "failed", errors, manifest, integrity, privacy, build_info)
        return 1
    try:
        exe_path = install_executable(root)
    except FileNotFoundError as exc:
        errors.append({"code": "PYINSTALLER_EXECUTABLE_MISSING", "message": str(exc)})
        write_module_artifacts(root, started_at, now_iso(), "failed", errors, manifest, integrity, privacy, build_info)
        return 1

    integrity = integrity_report(root)
    privacy = privacy_audit(root)
    zip_path = None if args.no_zip else create_zip(root)
    manifest = package_manifest(root, exe_path, release_meta, zip_path)
    if privacy["status"] != "passed":
        errors.append({"code": "WINDOWS_PACKAGE_PRIVACY_AUDIT_FAILED", "message": "Privacy audit found forbidden packaged content."})
    write_release_manifests(root, manifest, integrity, privacy)
    integrity = integrity_report(root)
    if not args.no_zip:
        zip_path = create_zip(root)
        manifest = package_manifest(root, exe_path, release_meta, zip_path)
        write_release_manifests(root, manifest, integrity, privacy)
    status = "success" if not errors else "failed"
    write_module_artifacts(root, started_at, now_iso(), status, errors, manifest, integrity, privacy, build_info)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
