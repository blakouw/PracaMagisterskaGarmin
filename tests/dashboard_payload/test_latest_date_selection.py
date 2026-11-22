from dashboard_helpers import read_output
def test_latest(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["metadata"]["latest_date"] == "2026-01-03"

