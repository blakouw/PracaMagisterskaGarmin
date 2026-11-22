from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


MODULE_ID = "19_packaging_windows"
MISSING_MESSAGE = "Windows package artifacts do not exist. Run pipeline/19_packaging_windows/run.bat first."


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview Windows packaging artifacts.")
    parser.add_argument("--show-files", action="store_true")
    parser.add_argument("--show-privacy", action="store_true")
    args = parser.parse_args(argv)
    root = root_dir()
    artifact = root / "data" / "pipeline" / MODULE_ID
    required = [
        artifact / "windows_package_manifest.json",
        artifact / "windows_package_integrity.json",
        artifact / "windows_package_privacy_audit.json",
        artifact / "windows_package_quality_report.json",
        artifact / "run_manifest.json",
    ]
    if not all(path.is_file() for path in required):
        print(MISSING_MESSAGE)
        return 1
    manifest = read_json(required[0])
    integrity = read_json(required[1])
    privacy = read_json(required[2])
    quality = read_json(required[3])
    run_manifest = read_json(required[4])
    print("Windows Package")
    print(f"Status: {quality.get('status')}")
    print(f"Execution: {run_manifest.get('execution_status')}")
    print(f"Package: {manifest.get('package_directory')}")
    print(f"ZIP: {manifest.get('zip_path')}")
    runtime = manifest.get("runtime", {})
    print(f"Host: {runtime.get('host')}")
    print(f"Port: {runtime.get('port')}")
    print(f"Local only: {runtime.get('local_only')}")
    print(f"Uses Vite dev server: {runtime.get('uses_vite_dev_server')}")
    print(f"Serves API: {runtime.get('serves_api_v1')}")
    print(f"Serves static UI: {runtime.get('serves_static_ui')}")
    print(f"Private snapshots packaged: {privacy.get('private_snapshots_packaged')}")
    print(f"Tokens/secrets packaged: {privacy.get('tokens_or_secrets_packaged')}")
    print(f"Raw Garmin files packaged: {privacy.get('raw_garmin_files_packaged')}")
    print(f"Integrity files: {integrity.get('files_count')}")
    print(f"Ready for local use: {quality.get('ready_for_local_use')}")
    if args.show_privacy:
        print("Privacy findings:")
        for finding in privacy.get("findings", []):
            print(f"- {finding.get('type')}: {finding.get('path')}")
    if args.show_files:
        print("Packaged files:")
        for item in integrity.get("files", []):
            print(f"- {item.get('path')} ({item.get('size_bytes')} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
