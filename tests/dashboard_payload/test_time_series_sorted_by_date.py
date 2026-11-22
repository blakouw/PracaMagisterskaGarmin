from dashboard_helpers import read_output
def test_sorted(module15, fake_root):
    module15.build(fake_root)
    dates=[r["date"] for r in read_output(fake_root)["time_series"]]
    assert dates == sorted(dates)

