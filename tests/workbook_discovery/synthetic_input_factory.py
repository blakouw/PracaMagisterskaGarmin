from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "01_find_input_workbook"
MODULE_DIR = ROOT / "pipeline" / MODULE_ID
MODULE_PATH = MODULE_DIR / "main.py"
ARTIFACT_RELATIVE_DIR = Path("data") / "pipeline" / MODULE_ID


def read_project_json(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def load_module(name: str = "find_input_workbook_under_test") -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_settings(
    root: Path,
    *,
    search_directories: list[str] | None = None,
    filename_pattern: str = "garmin_export_*.xlsx",
    recursive: bool = False,
    selection_strategy: str = "first_path_sorted_ascending",
    require_exactly_one_match: bool = False,
) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    for directory in search_directories or [".", "data/input"]:
        if directory != "." and not Path(directory).is_absolute():
            (root / directory).mkdir(parents=True, exist_ok=True)
    payload = {
        "input_workbook": {
            "filename_pattern": filename_pattern,
            "search_directories": search_directories or [".", "data/input"],
            "recursive": recursive,
            "selection_strategy": selection_strategy,
            "require_exactly_one_match": require_exactly_one_match,
        }
    }
    (root / "config" / "project_settings.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def make_case_root(tmp_path: Path, *, search_directories: list[str] | None = None) -> Path:
    root = tmp_path / "synthetic_project"
    root.mkdir(parents=True)
    write_settings(root, search_directories=search_directories)
    return root


def create_file(root: Path, relative_path: str, data: bytes = b"") -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def artifact_dir(root: Path) -> Path:
    return root / ARTIFACT_RELATIVE_DIR


def artifact_json(root: Path, filename: str) -> dict[str, Any]:
    return json.loads((artifact_dir(root) / filename).read_text(encoding="utf-8"))


def artifact_text(root: Path, filename: str) -> str:
    return (artifact_dir(root) / filename).read_text(encoding="utf-8")


def execute(root: Path) -> int:
    return load_module(f"find_input_workbook_{root.name}").execute(root)


def manifest(root: Path) -> dict[str, Any]:
    return artifact_json(root, "workbook_manifest.json")


def selected_relative_path(root: Path) -> str | None:
    selected = manifest(root)["selected_workbook"]
    return None if selected is None else selected["relative_path"]


def all_artifact_text(root: Path) -> str:
    chunks: list[str] = []
    for path in sorted(artifact_dir(root).glob("*")):
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)
