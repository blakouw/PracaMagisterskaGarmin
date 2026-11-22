from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "18_angular_dashboard_ui"
MODULE_DIR = ROOT / "pipeline" / MODULE_ID


def load_validate_module():
    spec = importlib.util.spec_from_file_location("ui18_validate", MODULE_DIR / "validate_ui_contract.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(MODULE_DIR))
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def validate_module():
    return load_validate_module()
