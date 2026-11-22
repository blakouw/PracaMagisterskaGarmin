from dashboard_helpers import read_output
def test_load_copied(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["current_state"]["load_metrics"]["acute_ewma_7d"] == 102

