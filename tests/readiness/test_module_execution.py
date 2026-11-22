from pathlib import Path
from .helpers09 import run_module, setup_root, base_record


def test_execute_function(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0


def test_run_bat_exists():
    root = Path(__file__).resolve().parents[2]
    assert (root / "pipeline/09_compute_readiness/run.bat").exists()
