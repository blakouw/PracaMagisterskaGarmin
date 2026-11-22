from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "19_packaging_windows"
MODULE_DIR = ROOT / "pipeline" / MODULE_ID


def load_packaging_module():
    spec = importlib.util.spec_from_file_location("packaging19_main", MODULE_DIR / "main.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def packaging_module():
    return load_packaging_module()
