from __future__ import annotations

import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def tmp_path(request):
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in request.node.nodeid)
    path = ROOT / "agenttmp" / "test_tmp" / f"{safe_name}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path
