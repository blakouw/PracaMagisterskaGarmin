from dashboard_helpers import read_output
def test_quality(module15, fake_root):
    module15.build(fake_root)
    q=read_output(fake_root)["quality_and_coverage"]
    assert q["presentation_availability"]["primary_pws_computed_count"] == 2
    assert q["coverage_tiers"]["insufficient"] == 1

