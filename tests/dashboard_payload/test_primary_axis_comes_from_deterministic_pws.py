from dashboard_helpers import read_output
def test_axis(module15, fake_root):
    module15.build(fake_root)
    assert [r["date"] for r in read_output(fake_root)["time_series"]] == ["2026-01-01","2026-01-02","2026-01-03"]

