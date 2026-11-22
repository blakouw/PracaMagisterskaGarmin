from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "17_local_api_server"
TEST_DIR = Path(__file__).resolve().parent
MODULE_DIR = ROOT / "pipeline" / MODULE_ID
for path in [TEST_DIR, MODULE_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_module(name: str):
    path = MODULE_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"api17_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    sys.path.insert(0, str(MODULE_DIR))
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def tmp_path(request):
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in request.node.name)
    path = ROOT / "agenttmp" / "tests_17_local_api_server" / f"{safe_name}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def api_app_module():
    return load_module("api_app")


@pytest.fixture()
def main_module():
    return load_module("main")
