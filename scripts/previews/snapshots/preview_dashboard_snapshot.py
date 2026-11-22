from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MODULE_ID = "16_persist_local_snapshot"
ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = ROOT / "data" / "pipeline" / MODULE_ID
SNAPSHOT_ROOT = ROOT / "data" / "published" / "dashboard_snapshots"
CURRENT_DIR = SNAPSHOT_ROOT / "current"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    paths = [
        PIPELINE_DIR / "snapshot_publication.json",
        PIPELINE_DIR / "snapshot_publication_quality_report.json",
        CURRENT_DIR / "snapshot_manifest.json",
        CURRENT_DIR / "snapshot_status.json",
        CURRENT_DIR / "snapshot_source_hashes.json",
    ]
    if not all(path.is_file() for path in paths):
        print("Published dashboard snapshot artifacts do not exist. Run pipeline/16_persist_local_snapshot/run.bat first.")
        raise SystemExit(1)
    return tuple(read_json(path) for path in paths)  # type: ignore[return-value]


def show_history(limit: int) -> None:
    history_root = SNAPSHOT_ROOT / "history"
    if not history_root.is_dir():
        print("History snapshots: none")
        return
    dirs = sorted([path for path in history_root.iterdir() if path.is_dir()], reverse=True)[:limit]
    print("History snapshots:")
    for path in dirs:
        manifest_path = path / "snapshot_manifest.json"
        if manifest_path.is_file():
            manifest = read_json(manifest_path)
            print(f"- {path.name} published_at={manifest.get('published_at')} latest_data_date={manifest.get('latest_data_date')}")
        else:
            print(f"- {path.name} manifest=missing")


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview published dashboard snapshot metadata.")
    parser.add_argument("--show-current", action="store_true")
    parser.add_argument("--show-history", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-hashes", action="store_true")
    parser.add_argument("--show-status", action="store_true")
    parser.add_argument("--show-manifest", action="store_true")
    args = parser.parse_args()

    publication, quality, manifest, status, hashes = require_artifacts()
    print(f"Module: {MODULE_ID}")
    print(f"Publication status: {publication.get('status')}")
    print(f"Snapshot ID: {publication.get('snapshot_id')}")
    print(f"Published at: {publication.get('published_at')}")
    print(f"Latest data date: {publication.get('latest_data_date')}")
    print(f"History snapshot: {publication.get('published_paths', {}).get('history_snapshot')}")
    print(f"Current snapshot: {publication.get('published_paths', {}).get('current_snapshot')}")
    print(f"History written: {publication.get('publication_result', {}).get('history_snapshot_written')}")
    print(f"Current published: {publication.get('publication_result', {}).get('current_snapshot_published')}")
    print(f"Hashes verified: {hashes.get('all_required_hashes_verified')} / optional={hashes.get('all_present_optional_hashes_verified')}")
    print("Published files:")
    for item in manifest.get("files", []):
        print(f"- {item.get('filename')} required={item.get('required')} included={item.get('included', True)}")
    parquet = next((item for item in manifest.get("files", []) if item.get("filename") == "dashboard_time_series.parquet"), {})
    print(f"Optional Parquet included: {parquet.get('included', False)}")
    print(f"Primary deterministic PWS: {status.get('primary_pws')}")
    print(f"Optional assisted PWS: {status.get('optional_assisted_pws')}")
    print("Assisted score replaces primary: false")
    print(f"Analytical values recomputed: {publication.get('payload_preservation_confirmation', {}).get('analytical_values_recomputed')}")
    print(f"LLM called: {publication.get('payload_preservation_confirmation', {}).get('llm_called')}")
    print("Snapshot privacy: private local derived wellness artifact")
    print(f"Ready for future API/UI: {publication.get('ready_for_next_module')}")

    if args.show_current:
        print(f"Current directory: {CURRENT_DIR.relative_to(ROOT).as_posix()}")
    if args.show_hashes:
        print(json.dumps(hashes, indent=2, ensure_ascii=False))
    if args.show_status:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    if args.show_manifest:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    if args.show_history:
        show_history(args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
