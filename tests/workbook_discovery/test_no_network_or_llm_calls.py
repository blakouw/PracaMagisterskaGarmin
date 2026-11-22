from __future__ import annotations

import socket
from pathlib import Path

import pytest

from synthetic_input_factory import create_file, execute, make_case_root


def test_execution_does_not_open_network_sockets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = make_case_root(tmp_path)
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    def blocked_socket(*args, **kwargs):
        raise AssertionError("Module 01 must not perform network calls")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    assert execute(root) == 0


def test_module_source_does_not_use_network_or_llm_clients() -> None:
    source = (Path(__file__).resolve().parents[2] / "pipeline" / "01_find_input_workbook" / "main.py").read_text(
        encoding="utf-8"
    ).lower()
    forbidden_terms = ["garminconnect", "openai", "requests", "httpx", "urllib", "socket", "api_key"]
    assert [term for term in forbidden_terms if term in source] == []
