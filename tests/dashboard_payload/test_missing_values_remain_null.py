from dashboard_helpers import read_output
def test_nulls(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["time_series"][2]["pws_deterministic"] is None
    assert read_output(fake_root)["time_series"][2]["rec_score"] is None

