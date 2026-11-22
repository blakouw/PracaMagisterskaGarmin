from __future__ import annotations

import shutil
import subprocess

from registry_helpers import ROOT


SYNTHETIC_PRIVATE_PATHS = [
    "data/input/example_private_export.xlsx",
    "data/local_secrets/example_token.json",
    "data/local_context/example_context.json",
    "data/pipeline/08_compute_load_metrics/private.csv",
    "data/pipeline/12_compute_pws_score/private.parquet",
    "data/published/dashboard_snapshots/current/dashboard_payload.json",
    "release/windows/example_portable.zip",
    "example.fit",
    "example.tcx",
    "garmin_export_2099-01-01.xlsx",
    "pipeline/18_angular_dashboard_ui/app/node_modules/example.js",
    "pipeline/18_angular_dashboard_ui/app/dist/index.html",
    ".coverage",
]


def gitignore_text() -> str:
    return (ROOT / ".gitignore").read_text(encoding="utf-8")


def test_gitignore_contains_private_data_protection_rules() -> None:
    text = gitignore_text().replace("\\", "/")
    required_fragments = [
        "data/input/*.xlsx",
        "data/local_secrets/",
        "data/local_context/",
        "data/pipeline/**/*.csv",
        "data/pipeline/**/*.parquet",
        "data/published/dashboard_snapshots/",
        "release/windows/",
        "*.fit",
        "*.tcx",
        "garmin_export_*.xlsx",
        "*.log",
        "node_modules/",
        "app/dist/",
        ".coverage",
    ]
    for fragment in required_fragments:
        assert fragment in text, fragment


def test_public_contract_and_policy_files_are_not_blanket_ignored() -> None:
    text = gitignore_text().replace("\\", "/")
    for fragment in [
        "!config/project_settings.json",
        "!config/pipeline_modules.json",
        "!config/dashboard_snapshot_api_policy_v1.json",
        "!config/local_dashboard_ui_policy_v1.json",
        "!config/windows_packaging_policy_v1.json",
    ]:
        assert fragment in text, fragment


def test_git_check_ignore_for_synthetic_private_paths_when_available() -> None:
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        return
    result = subprocess.run(
        ["git", "check-ignore", *SYNTHETIC_PRIVATE_PATHS],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    ignored = set(result.stdout.strip().splitlines())
    assert set(SYNTHETIC_PRIVATE_PATHS) <= ignored
