from dashboard_helpers import read_output
def test_no_recompute(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["quality_and_coverage"]["recomputation_confirmation"]["pws_deterministic_recomputed"] is False

