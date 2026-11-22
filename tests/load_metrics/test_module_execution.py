import subprocess
import sys
from .helpers08 import make_records, setup_root


def test_main_execute_function_supports_independent_root(tmp_path):
    from .helpers08 import run_module

    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0


def test_run_bat_exists():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    assert (root / "pipeline/08_compute_load_metrics/run.bat").exists()
