from pathlib import Path
from .helpers10 import run_module, setup_root


def test_execute_function(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0


def test_run_bat_exists():
    root = Path(__file__).resolve().parents[2]
    assert (root / "pipeline/10_compute_pws_components/run.bat").exists()
