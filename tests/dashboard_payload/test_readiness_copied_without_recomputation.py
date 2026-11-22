from dashboard_helpers import read_output
def test_readiness_copied(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["time_series"][0]["readiness_score"] == 86.0

