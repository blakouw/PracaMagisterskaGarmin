from __future__ import annotations

import re

from registry_helpers import ROOT, file_text, public_text_files, read_json


PREVIOUS_PROJECT_PATH_PATTERNS = [
    re.compile(r"C:\\Users\\[^\\]+\\Documents\\RepoMagi", re.IGNORECASE),
    re.compile(r"\.\.\\RepoMagi", re.IGNORECASE),
    re.compile(r"\.\./RepoMagi", re.IGNORECASE),
]
ACTIVE_RUNTIME_PATTERNS = [
    re.compile(r"from\s+RepoMagi\b"),
    re.compile(r"import\s+RepoMagi\b"),
    re.compile(r"subprocess\.(?:run|Popen|call)\([^)]*RepoMagi", re.IGNORECASE | re.DOTALL),
    re.compile(r"Start-Process[^\n]*RepoMagi", re.IGNORECASE),
]


def test_project_settings_disallow_previous_project_runtime_dependency() -> None:
    settings = read_json("config/project_settings.json")
    assert settings["previous_project_runtime_dependency_allowed"] is False


def test_public_code_has_no_hardcoded_previous_project_paths_or_imports() -> None:
    offenders: list[str] = []
    for path in public_text_files():
        if path.name == "test_runtime_isolation.py":
            continue
        text = file_text(path)
        for pattern in PREVIOUS_PROJECT_PATH_PATTERNS + ACTIVE_RUNTIME_PATTERNS:
            if pattern.search(text):
                offenders.append(path.relative_to(ROOT).as_posix())
                break
    assert offenders == []


def test_previous_project_mentions_do_not_require_runtime_presence() -> None:
    requiring_runtime_patterns = [
        re.compile(r"requires?\s+.{0,80}(?:RepoMagi|previous project)", re.IGNORECASE),
        re.compile(
            r"must\s+(?!not\b).{0,80}(?:load|import|execute|run|call)\s+.{0,80}(?:RepoMagi|previous project)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:RepoMagi|previous project)\s+.{0,80}(?:required at runtime|required runtime)",
            re.IGNORECASE,
        ),
    ]
    offenders: list[str] = []
    for path in public_text_files():
        if path.name == "test_runtime_isolation.py":
            continue
        text = file_text(path)
        if "previous project" not in text.lower() and "repomagi" not in text.lower():
            continue
        lines = [
            re.sub(r"\b(?:it\s+)?must\s+not\b[^.]*previous project[^.]*", "", line, flags=re.IGNORECASE)
            for line in text.splitlines()
        ]
        for pattern in requiring_runtime_patterns:
            if any(pattern.search(line) for line in lines):
                offenders.append(path.relative_to(ROOT).as_posix())
                break
    assert offenders == []
