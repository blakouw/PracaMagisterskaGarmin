from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "16_persist_local_snapshot"
TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))


@pytest.fixture()
def snapshot_module():
    path = ROOT / "pipeline" / MODULE_ID / "main.py"
    spec = importlib.util.spec_from_file_location("snapshot16_main", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
