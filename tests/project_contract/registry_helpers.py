from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
REMOVED_MODULE_IDS = {"auth_and_profile_api", "garmin_token_pipeline"}
PRIVATE_OR_GENERATED_PARTS = {
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "coverage",
    "build",
    "release",
    "data",
    ".tmp",
    ".tmp_test",
    ".tmp_agent_pytest",
    "agenttmp",
    "agenttmp2",
}
PUBLIC_TEXT_SUFFIXES = {".py", ".bat", ".json", ".md", ".txt", ".ini", ".toml", ".css", ".tsx", ".ts", ".html"}


def read_json(relative_path: str | Path) -> Any:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def registry() -> dict[str, Any]:
    return read_json("config/pipeline_modules.json")


def registry_modules() -> list[dict[str, Any]]:
    return registry()["modules"]


def modules_by_id() -> dict[str, dict[str, Any]]:
    return {module["id"]: module for module in registry_modules()}


def contract(module_id: str) -> dict[str, Any]:
    return read_json(Path("pipeline") / module_id / "contract.json")


def module_ids() -> list[str]:
    return [module["id"] for module in registry_modules()]


def implemented_module_ids() -> set[str]:
    return {module["id"] for module in registry_modules() if module["status"] == "implemented"}


def planned_module_ids() -> set[str]:
    return {module["id"] for module in registry_modules() if module["status"] == "planned"}


def normalize_path(path: str | Path) -> str:
    return Path(path).as_posix().strip("/")


def public_text_files() -> Iterable[Path]:
    roots = [ROOT / "config", ROOT / "pipeline", ROOT / "tests", ROOT / "visualization"]
    root_files = [ROOT / ".gitignore", ROOT / "pytest.ini", ROOT / "requirements.txt"]
    for path in root_files:
        if path.is_file():
            yield path
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in PUBLIC_TEXT_SUFFIXES:
                continue
            rel_parts = set(path.relative_to(ROOT).parts)
            if rel_parts & PRIVATE_OR_GENERATED_PARTS:
                continue
            yield path


def file_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def all_public_text() -> str:
    return "\n".join(file_text(path) for path in public_text_files())


def module_exists(module_id: str) -> bool:
    return (ROOT / "pipeline" / module_id).is_dir()


def implemented_contracts() -> dict[str, dict[str, Any]]:
    return {module_id: contract(module_id) for module_id in implemented_module_ids()}
