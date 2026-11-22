from __future__ import annotations

import re
from pathlib import Path

from synthetic_input_factory import MODULE_DIR, ROOT


def test_module_01_and_its_tests_have_no_previous_project_runtime_dependency() -> None:
    scan_roots = [MODULE_DIR, Path(__file__).resolve().parent]
    active_patterns = [
        re.compile(r"from\s+RepoMagi\b"),
        re.compile(r"import\s+RepoMagi\b"),
        re.compile(r"C:\\Users\\[^\\]+\\Documents\\RepoMagi", re.IGNORECASE),
        re.compile(r"\.\.[/\\]RepoMagi", re.IGNORECASE),
        re.compile(r"subprocess\.(?:run|Popen|call)\([^)]*RepoMagi", re.IGNORECASE | re.DOTALL),
        re.compile(r"fallback[^.\n]*(?:RepoMagi|previous project)", re.IGNORECASE),
    ]
    offenders: list[str] = []

    for root in scan_roots:
        for path in root.rglob("*"):
            if path.is_dir() or path.suffix.lower() not in {".py", ".bat", ".json", ".md"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern.search(text) for pattern in active_patterns):
                offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == []
